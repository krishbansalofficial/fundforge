"""Model-based test: random command sequences from both partners (and an outsider) against Session.

After every step: the books reconcile, a rejected command changed nothing, every live
order is authorized (PM ticket or a package signed by both partners), and at teardown a
fresh replay of the accepted log reproduces the same journal digest.
"""

from pathlib import Path

from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import load

TAPE = load(Path(__file__).parents[2] / "fixtures" / "case1.json")
PARTNERS = {"pm": "ana", "mp": "ben"}
USERS = st.sampled_from(["ana", "ben", "mallory"])
SYMS = st.sampled_from(["BEAM", "ALTO", "BRIN", "DART", "BOND"])
SIDES = st.sampled_from(["BUY", "SELL", "SHORT", "COVER"])
QTY = st.sampled_from([1, 500, 2_000, 12_000, 20_000])


def fresh() -> Session:
    e = Engine(TAPE)
    e.advance()
    return Session(e, dict(PARTNERS))


class SessionMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.s = fresh()
        self.accepted: list[tuple[str, str, dict]] = []
        self.tickets: set[str] = set()
        self.n = 0

    def _snapshot(self):
        e = self.s.e
        return (e.j.digest(), [(o.order_id, o.status, o.filled) for o in e.orders],
                {k: (p.status, frozenset(p.signatures)) for k, p in self.s.packages.items()}, e.cursor)

    def send(self, user, cmd, key=None):
        self.n += 1
        key = key or f"k{self.n}"
        before = self._snapshot()
        try:
            result = self.s.handle(user, key, cmd)
        except CommandRejected:
            assert self._snapshot() == before, f"rejected {cmd['type']} mutated state"
            return None
        if not any(k == key for _, k, _ in self.accepted):
            self.accepted.append((user, key, cmd))
        return result

    @rule(user=USERS, sym=SYMS, side=SIDES, qty=QTY)
    def ticket(self, user, sym, side, qty):
        oid = f"t{self.n}"
        if self.send(user, {"type": "ticket", "order_id": oid, "sym": sym, "side": side, "qty": qty}):
            self.tickets.add(oid)

    @rule(user=USERS, sym=SYMS, side=SIDES, qty=QTY)
    def propose(self, user, sym, side, qty):
        self.send(user, {"type": "propose", "package_id": f"p{self.n}",
                         "orders": [{"order_id": f"po{self.n}", "sym": sym, "side": side, "qty": qty}]})

    @rule(user=USERS, data=st.data())
    def sign(self, user, data):
        if self.s.packages:
            p = data.draw(st.sampled_from(sorted(self.s.packages)))
            digest = data.draw(st.sampled_from([self.s.packages[p].digest, "0" * 64]))
            self.send(user, {"type": "sign", "package_id": p, "digest": digest})

    @rule(user=USERS, topic=st.sampled_from(["borrow", "debt_schedule", "demand_survey", "nope"]))
    def research(self, user, topic):
        self.send(user, {"type": "research", "topic": topic})

    @rule(user=USERS)
    def accept(self, user):
        self.send(user, {"type": "accept_replacement"})

    @rule(user=USERS, amount=st.sampled_from(["0", "500000", "1250000"]))
    def reserve(self, user, amount):
        self.send(user, {"type": "set_reserve", "amount": amount})

    @rule(user=USERS, stale=st.booleans())
    def ready(self, user, stale):
        self.send(user, {"type": "ready", "version": self.s.version - (1 if stale else 0)})

    @rule()
    def both_ready(self):
        self.send("ana", {"type": "ready", "version": self.s.version})
        self.send("ben", {"type": "ready", "version": self.s.version})

    @rule(data=st.data())
    def retry_same_key(self, data):
        if self.accepted:
            user, key, cmd = data.draw(st.sampled_from(self.accepted))
            before = self._snapshot()
            self.s.handle(user, key, cmd)  # retry: same result, no new effect
            assert self._snapshot() == before

    @rule(data=st.data())
    def reuse_key_for_other_command(self, data):
        if self.accepted:
            user, key, _ = data.draw(st.sampled_from(self.accepted))
            assert self.send(user, {"type": "research", "topic": "borrow-x"}, key=key) is None

    @invariant()
    def books_reconcile(self):
        self.s.e.reconcile()

    @invariant()
    def every_live_order_is_authorized(self):
        signed = {o[0] for p in self.s.packages.values() if p.signatures == {"pm", "mp"} for o in p.orders}
        for o in self.s.e.orders:
            assert o.forced or o.order_id in self.tickets or o.order_id in signed, o.order_id

    def teardown(self):
        r = fresh()
        for user, key, cmd in self.accepted:
            r.handle(user, key, cmd)
        assert r.e.j.digest() == self.s.e.j.digest()


SessionMachine.TestCase.settings = settings(max_examples=40, stateful_step_count=40, deadline=None,
                                            suppress_health_check=[HealthCheck.too_slow])
TestSession = SessionMachine.TestCase

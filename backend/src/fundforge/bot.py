"""Deterministic partner bot for solo play (owner decision, 8 Oct 2026).

The bot is a rules-based policy, not an LLM. It acts only through ordinary Session commands,
so it is bound by the same roles, digest signatures and mandate checks as a human, and its
actions are logged like any other command: replay never re-runs this policy.
"""

from decimal import Decimal
from typing import Any

from .engine import CommandRejected
from .governance import TICKET_NAV_LIMIT, Session
from .money import cents

BOT_VERSION = "bot:v1"
REFUSED = {  # package kinds the bot will not countersign, with the reason it says instead
    "gate": "I won't elect a redemption gate: that needs a human partner's consent.",
    "winddown": "I won't declare a winddown: ending the fund needs a human partner's consent.",
}


def _said(s: Session, ref: str) -> bool:
    return any(m.get("ref") == ref for m in s.chat)


def _open_orders(s: Session, sym: str, side: str) -> int:
    return sum(o.remaining for o in s.e.orders
               if o.sym == sym and o.side == side and o.status in ("QUEUED", "PARTIALLY_FILLED"))


def plan(s: Session, role: str) -> list[dict[str, Any]]:
    """Commands the bot wants to send now, in order. Pure function of the session state."""
    e = s.e
    out: list[dict[str, Any]] = []
    if e.finished():
        return out
    at_barrier = e.at_barrier()
    # 1. review the human partner's packages: countersign or explain the refusal
    for p in s.packages.values():
        if p.status == "PENDING_APPROVAL" and p.proposer != role and not _said(s, f"pkg:{p.package_id}"):
            # material exceptions need distinct human consent; the bot never supplies it
            if p.kind in REFUSED:
                out.append({"type": "say", "ref": f"pkg:{p.package_id}", "text": REFUSED[p.kind]})
                continue
            out.append({"type": "sign", "package_id": p.package_id, "digest": p.digest,
                        "_ref": f"pkg:{p.package_id}"})
    if role == "mp" and at_barrier:
        for issue in e.broker.queue(e.ev.date, e.ev.day):
            if issue["can_resolve"]:
                out.append({"type": "resolve_statement", "statement_id": issue["id"],
                            "revision": issue["revision"], "version": s.version,
                            "_ref": f"statement:{issue['id']}:{issue['revision']}",
                            "_say": "I reviewed the broker correction. The original statement remains in RISK."})
        # 2. operating partner: check the borrow before the recall bites
        if not any(r["topic"] == "borrow" for r in e.research_used) and not _said(s, "research:borrow"):
            out.append({"type": "research", "topic": "borrow", "_ref": "research:borrow",
                        "_say": "I've asked the desk to check BRIN lending; results at tomorrow's open."})
        if e.offer_visible and "borrow" not in e.shared_research:
            out.append({"type": "share_research", "topic": "borrow", "_ref": "share:borrow",
                        "_say": "I've shared the borrow evidence; you can read it at the research desk."})
        brin_cover = _open_orders(s, "BRIN", "COVER")
        if (e.offer_visible and not e.replacement_accepted and e.recall_open > brin_cover
                and not _said(s, "accept:replacement")):
            out.append({"type": "accept_replacement", "_ref": "accept:replacement",
                        "_say": "I accepted the 1,250 BRIN replacement borrow at 40%: it keeps the short "
                                "but costs carry until we cover. Cover it whenever you like."})
    if role == "pm" and at_barrier:
        nav = e.nav()
        cap = cents(nav * TICKET_NAV_LIMIT)
        # 3. portfolio manager: never let the recall reach a forced buy-in
        brin_short = -e.pos.get("BRIN", 0)
        need = min(e.recall_open, brin_short) - _open_orders(s, "BRIN", "COVER")
        if need > 0 and not e.replacement_accepted:
            out.append({"type": "ticket", "order_id": f"bot-cover-{e.ev.day}", "sym": "BRIN", "side": "COVER",
                        "qty": need, "_ref": f"cover:{e.ev.day}",
                        "_say": f"Covering {need:,} recalled BRIN now so the broker never buys us in."})
        # 4. cure a margin call with the most liquid single-name long, within my ticket limit
        if e.margin_call and not any(o.side == "SELL" and o.status == "QUEUED" and not o.forced for o in e.orders):
            longs = sorted((sym for sym, q in e.pos.items() if q > 0 and sym not in e.mandate.issuer_exempt),
                           key=lambda sym: (-e.pos[sym], sym))
            if longs:
                sym = longs[0]
                relief = Decimal("0.68") * e.marks[sym]
                qty = min(int(e.margin_call / relief) + 1, int(cap / e.marks[sym]), e.pos[sym])
                out.append({"type": "ticket", "order_id": f"bot-cure-{e.ev.day}-{e.ev.phase}", "sym": sym,
                            "side": "SELL", "qty": qty, "_ref": f"cure:{e.ev.day}:{e.ev.phase}",
                            "_say": f"Margin call: selling {qty:,} {sym} to restore headroom."})
    # 5. keep pace: ready whenever the human partner is
    if (set(s.ready) - {role}) and role not in s.ready:
        out.append({"type": "ready", "version": None} | ({"skip": True} if all(s.ready.values()) else {}))
    return out


def act(s: Session, role: str, user: str, key_prefix: str) -> list[tuple]:
    """Run the bot until it has nothing to do. Returns, for each accepted command,
    (key, command, result, (journal_lo, journal_hi, journal_digest_after))."""
    done: list[tuple] = []

    def run(key: str, cmd: dict[str, Any]) -> dict[str, Any]:
        lo = len(s.e.j.entries)
        result = s.handle(user, key, cmd)
        done.append((key, cmd, result, (lo, len(s.e.j.entries), s.e.j.digest())))
        return result

    for _round in range(6):  # bounded: each pass either acts or stops
        cmds = plan(s, role)
        if not cmds:
            break
        acted = False
        for i, c in enumerate(cmds):
            ref, say = c.pop("_ref", None), c.pop("_say", None)
            if c["type"] in ("ready", "resolve_statement"):
                c["version"] = s.version
            key = f"{key_prefix}-{_round}-{i}"
            try:
                run(key, c)
                acted = True
                text = say or (f"Countersigned your package {c['package_id']}: it fits the mandate."
                               if c["type"] == "sign" else None)
            except CommandRejected as ex:
                text = (f"I won't countersign {c['package_id']}: {ex}" if c["type"] == "sign"
                        else f"I tried to {c['type'].replace('_', ' ')} but couldn't: {ex}")
            if text and ref:
                note = {"type": "say", "text": text[:240], "ref": ref}
                run(f"{key}-say", note)
                acted = True
        if not acted:
            break
    return done

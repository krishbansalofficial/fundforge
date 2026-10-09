"""An endogenous market: rival hedge funds whose order flow moves prices.

The authored tape supplies exogenous news (shocks, halts, volumes). Every instrument also has
a permanent-impact multiplier driven by all participants' net order flow, which decays toward
1 between events (resilience). The price everyone trades and marks at is tape x multiplier.

Rivals are deterministic rule agents with their own books, cash and margin. They see only
public marks. A crowded short fund that breaches margin is forced to cover, which lifts the
names it is short: a squeeze emerges from the simulation instead of being scripted. A fund
whose NAV goes negative is liquidated over subsequent events (contagion through prices).
"""

from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from .money import CTX, D

CAP = Decimal("0.15")  # max cumulative impact either way


@dataclass
class Rival:
    rival_id: str
    name: str
    style: str
    cash: Decimal
    pos: dict[str, int]
    params: dict = field(default_factory=dict)
    status: str = "active"  # active | deleveraging | liquidating | closed
    start_nav: Decimal = Decimal(0)

    def mv(self, marks):
        return sum((q * marks[s] for s, q in self.pos.items()), Decimal(0))

    def nav(self, marks) -> Decimal:
        with localcontext(CTX):
            return self.cash + self.mv(marks)


class Market:
    def __init__(self, raw: dict | None, instruments: list[str]):
        raw = raw or {}
        self.impact = D(raw.get("impact", "0"))
        self.resilience = D(raw.get("resilience", "0.25"))
        self.max_participation = D(raw.get("max_participation", "0.10"))
        self.mult: dict[str, Decimal] = {s: Decimal(1) for s in instruments}
        self.rivals = [Rival(r["id"], r["name"], r["style"], D(r["cash"]), dict(r["positions"]), dict(r.get("params", {})))
                       for r in raw.get("funds", [])]
        self.last_flow: dict[str, int] = {}

    # ---------- prices ----------
    def effective(self, tape_marks: dict[str, Decimal]) -> dict[str, Decimal]:
        with localcontext(CTX):
            return {s: (m * self.mult[s]).quantize(Decimal("0.000001")) for s, m in tape_marks.items()}

    def decay(self):
        with localcontext(CTX):
            for s, m in self.mult.items():
                self.mult[s] = m + (1 - m) * self.resilience

    def push(self, flow: dict[str, int], volume: dict[str, int]):
        """Permanent impact from signed share flow (buys positive)."""
        with localcontext(CTX):
            for s, q in flow.items():
                v = volume.get(s, 0)
                if q and v:
                    m = self.mult[s] * (1 + self.impact * Decimal(q) / Decimal(v))
                    self.mult[s] = min(max(m, 1 - CAP), 1 + CAP)

    # ---------- rival behaviour ----------
    def init_navs(self, marks):
        for r in self.rivals:
            r.start_nav = r.nav(marks)

    def trade(self, marks: dict[str, Decimal], prev: dict[str, Decimal], volume: dict[str, int],
              margin: dict) -> tuple[dict[str, int], list[dict]]:
        """Each rival decides from public marks; returns total signed flow and notices."""
        flow: dict[str, int] = {}
        notices: list[dict] = []
        caps = {s: int(v * self.max_participation) for s, v in volume.items()}
        with localcontext(CTX):
            for r in self.rivals:
                if r.status == "closed":
                    continue
                orders = self._decide(r, marks, prev, margin, notices)
                for s, q in orders:
                    room = caps.get(s, 0) - abs(flow.get(s, 0))
                    q = max(-room, min(room, q)) if room > 0 else 0
                    if q == 0 or (q < 0 and r.pos.get(s, 0) + q < 0 and r.style != "crowded_short"):
                        continue
                    r.pos[s] = r.pos.get(s, 0) + q
                    r.cash -= q * marks[s]
                    flow[s] = flow.get(s, 0) + q
                if r.status == "liquidating" and all(q == 0 for q in r.pos.values()):
                    r.status = "closed"
                    notices.append({"code": "rival_closed", "rival": r.name,
                                    "text": f"{r.name} has finished liquidating and returned what was left to investors."})
        self.last_flow = flow
        return flow, notices

    def _decide(self, r: Rival, marks, prev, margin, notices) -> list[tuple[str, int]]:
        nav = r.nav(marks)
        long_mv = sum((q * marks[s] for s, q in r.pos.items() if q > 0), Decimal(0))
        short_mv = sum((-q * marks[s] for s, q in r.pos.items() if q < 0), Decimal(0))
        req = margin["maintenance"]["long"] * long_mv + margin["maintenance"]["short"] * short_mv
        if r.status != "liquidating" and nav <= 0:
            r.status = "liquidating"
            notices.append({"code": "rival_blowup", "rival": r.name,
                            "text": f"{r.name} has blown up and is liquidating its entire book."})
        if r.status == "liquidating":
            return [(s, -q) for s, q in sorted(r.pos.items()) if q]
        if nav < req:
            if r.status != "deleveraging":
                notices.append({"code": "rival_deleveraging", "rival": r.name,
                                "text": f"{r.name} is meeting a margin call and cutting its book."})
            r.status = "deleveraging"
            cut = D(r.params.get("deleverage", "0.35"))
            return [(s, -int(q * cut)) for s, q in sorted(r.pos.items()) if q and not (q > 0 and s == "BOND")]
        if r.status == "deleveraging":
            r.status = "active"
        rets = {s: (marks[s] / prev[s] - 1) if prev.get(s) else Decimal(0) for s in marks}
        size = D(r.params.get("size", "0.02")) * nav
        out: list[tuple[str, int]] = []
        if r.style == "momentum":
            for s in sorted(marks):
                if abs(rets[s]) > Decimal("0.01"):
                    out.append((s, int(size / marks[s]) * (1 if rets[s] > 0 else -1)))
        elif r.style == "mean_reversion":
            for s in sorted(marks):
                if abs(rets[s]) > Decimal("0.01"):
                    out.append((s, int(size / marks[s]) * (-1 if rets[s] > 0 else 1)))
        elif r.style == "macro":
            b = rets.get("BEAM", Decimal(0))
            if abs(b) > Decimal("0.02"):
                q = int(size * 3 / marks["BEAM"])
                out += [("BEAM", -q if b < 0 else q), ("BOND", int(size * 3 / marks["BOND"]) * (1 if b < 0 else -1))]
        elif r.style == "activist":
            dd = nav / r.start_nav - 1 if r.start_nav else Decimal(0)
            if dd < -D(r.params.get("pain", "0.08")):
                out += [(s, -int(q * Decimal("0.3"))) for s, q in sorted(r.pos.items()) if q > 0]
        return out

    # ---------- public information ----------
    def league(self, marks) -> list[dict]:
        with localcontext(CTX):
            rows = []
            for r in self.rivals:
                nav = r.nav(marks)
                ret = (nav / r.start_nav - 1) * 10000 if r.start_nav else Decimal(0)
                rows.append({"id": r.rival_id, "name": r.name, "style": r.style, "status": r.status,
                             "return_bps": str(ret.quantize(Decimal("0.1"))), "nav": str(nav.quantize(Decimal("1")))})
            return rows

    def crowding_report(self, marks, own_pos: dict[str, int]) -> str:
        """Prime-broker crowding report: who is short what (published only when the research is assigned)."""
        lines = []
        with localcontext(CTX):
            for s in sorted(marks):
                shorts = [(r.name, -r.pos.get(s, 0)) for r in self.rivals if r.pos.get(s, 0) < 0]
                total = sum(q for _, q in shorts) + max(0, -own_pos.get(s, 0))
                if total > 0 and shorts:
                    top = max(shorts, key=lambda x: x[1])
                    lines.append(f"{s}: {total:,} shares short across the street; {top[0]} alone holds {top[1]:,}")
        return "Crowding report: " + ("; ".join(lines) if lines else "no crowded shorts") + "."

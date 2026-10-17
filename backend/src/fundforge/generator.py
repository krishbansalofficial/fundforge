"""Seeded market generator (ROADMAP P4): ``generate(seed, gen_version, skeleton, spec) -> raw``.

Randomness is a SHA-256 counter stream: draw ``n`` hashes ``gen_version|seed|n`` and turn them
into integers by rejection sampling (no modulo bias, no floats). Shocks are whole basis points,
so every price step is exact Decimal arithmetic, quantized once to 6dp HALF_EVEN.

The skeleton's authored overrides (crisis marks, volumes, headlines) are fixed hidden inputs and
are never changed. Each unauthored ``PUBLIC_MARK`` gets one market-factor shock (scaled by
the current calm/stressed regime and each instrument's beta) plus an idiosyncratic shock;
later days continue from whatever the last authored or generated mark was. The output records
only a SHA-256 commitment to the seed; the seed stays server-side until the debrief, when
anyone can check it against the commitment and regenerate the tape.

Each generated day also prints a fictional Street activity index: the hidden regime's level plus
noise, published the next day. Some prints get a more accurate revision three days later. It reads
a separate ``MACRO_VERSION`` stream, so adding it never changes the generated marks.

``SCENARIO_VERSION`` adds a scenario randomiser (``randomise``) that runs before the marks: crisis
day, crisis severity, stressed margin terms, the scheduled LP redemption, rival parameters and the
opening book. ``GEN_VERSION`` is unchanged and still reproduces its old tapes byte for byte.
See docs/RANDOMISER.md.

Pure domain: no I/O. Acceptance through the balance runner is a separate step.
"""

import copy
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any, Literal

from .money import CTX

GEN_VERSION = "gen-2026.10.1"
SCENARIO_VERSION = "gen-2026.10.2"  # the scenario randomiser plus the marks generator
RANDOMISED = frozenset({SCENARIO_VERSION})
MACRO_VERSION = "macro-2026.10.2"
MACRO_SERIES = "STREET_ACTIVITY"
TENTH = Decimal("0.1")
PRICE = Decimal("0.000001")
BP = Decimal("0.0001")
SPLIT_SALT = "fundforge-split-v1"  # same salt as the ML package's contracts.split_of (ml/)


class Stream:
    """Deterministic integers from SHA-256(gen_version|seed|counter)."""

    def __init__(self, seed: str, gen_version: str):
        self.prefix = f"{gen_version}|{seed}|".encode()
        self.counter = 0

    def _word(self) -> int:
        digest = hashlib.sha256(self.prefix + str(self.counter).encode()).digest()
        self.counter += 1
        return int.from_bytes(digest[:8], "big")

    def integer(self, lo: int, hi: int) -> int:
        """Uniform on [lo, hi] inclusive; rejects the top partial block so there is no modulo bias."""
        if hi < lo:
            raise ValueError("empty range")
        span = hi - lo + 1
        limit = (1 << 64) - (1 << 64) % span
        while True:
            w = self._word()
            if w < limit:
                return lo + w % span


@dataclass(frozen=True)
class Spec:
    factor_bp: int = 150  # calm market-factor shock bound per public mark
    stress_multiplier: int = 3  # stressed regime scales the factor bound
    idio_bp: int = 100  # idiosyncratic shock bound
    switch_bp: int = 1500  # probability (bp) of switching regime at each public mark
    beta: Mapping[str, Decimal] = field(default_factory=lambda: {"BOND": Decimal(0)})  # default beta is 1
    # Street activity index, in tenths of a point: calm prints near 52.5, stressed near 47.5.
    macro_level: int = 500
    macro_regime: int = 25
    # first print error bound; wider than half the calm/stressed gap, so a print in the overlap is ambiguous
    macro_first_noise: int = 40
    macro_revised_noise: int = 5  # revisions are closer to the hidden level
    macro_revise_bp: int = 3000  # probability (bp) that a print is revised
    macro_lag: int = 1  # days from the period to its first print
    macro_revision_lag: int = 3
    # scenario randomiser (used only by RANDOMISED versions)
    crisis_days: int = 1  # crisis day moves by up to this many days (marks, volumes, stressed margin)
    crisis_points: int = 2  # each crisis mark (long and short) moves by up to this many points
    margin_points: int = 5  # both stressed coefficient pairs move by up to this many points
    rival_pct: int = 20  # each rival parameter is scaled by 100 +/- this percent
    redemption_pct: int = 20  # the scheduled redemption is scaled by 100 +/- this percent, in 500-unit steps
    book_pct: int = 5  # each opening position is scaled by 100 +/- this percent, in 100-share steps

    def __post_init__(self) -> None:
        if min(self.factor_bp, self.idio_bp, self.switch_bp, self.stress_multiplier) < 0 or self.switch_bp > 10_000:
            raise ValueError("generator bounds must be non-negative and switch_bp at most 10000")
        if not 0 <= self.macro_revise_bp <= 10_000 or not 1 <= self.macro_lag < self.macro_revision_lag:
            # a same-day print would come before that day's mark
            raise ValueError("macro needs revise_bp in 0..10000 and 1 <= lag < revision lag")
        if (
            min(
                self.crisis_days,
                self.crisis_points,
                self.margin_points,
                self.rival_pct,
                self.redemption_pct,
                self.book_pct,
            )
            < 0
            or max(self.rival_pct, self.redemption_pct, self.book_pct) >= 100
        ):
            raise ValueError("randomiser bounds must be non-negative; percentages below 100")
        worst_beta = max([Decimal(1), *(abs(b) for b in self.beta.values())])
        if worst_beta * self.factor_bp * self.stress_multiplier + self.idio_bp >= 10_000:
            raise ValueError("a single step could take a mark to zero")


def commitment(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def generate(seed: str, gen_version: str, skeleton: dict[str, Any], spec: Spec | None = None) -> dict[str, Any]:
    """A new raw tape: the skeleton with generated public marks on every unauthored day."""
    spec = spec or Spec()
    scenario = None
    if gen_version in RANDOMISED:
        skeleton, scenario = randomise(seed, gen_version, skeleton, spec)
    rng = Stream(seed, gen_version)
    syms = list(skeleton["instruments"])
    cal = skeleton["calendar"]
    authored = {(o["day"], o["event"]): o for o in skeleton["overrides"]}
    marks = {s: Decimal(skeleton["defaults"]["mark"]) for s in syms}
    stressed = False
    generated: list[dict[str, Any]] = []
    with localcontext(CTX):
        for day in range(cal["start_day"], cal["end_day"]):
            for event in ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE"):
                fixed = authored.get((day, event), {}).get("marks", {})
                marks.update({s: Decimal(v) for s, v in fixed.items()})
                if event != "PUBLIC_MARK" or fixed:
                    continue
                if rng.integer(0, 9_999) < spec.switch_bp:
                    stressed = not stressed
                bound = spec.factor_bp * (spec.stress_multiplier if stressed else 1)
                factor = rng.integer(-bound, bound) * BP
                for s in syms:
                    step = spec.beta.get(s, Decimal(1)) * factor + rng.integer(-spec.idio_bp, spec.idio_bp) * BP
                    marks[s] = (marks[s] * (1 + step)).quantize(PRICE, rounding=ROUND_HALF_EVEN)
                generated.append(
                    {
                        "day": day,
                        "event": event,
                        "marks": {s: str(marks[s]) for s in syms},
                        "regime": "stressed" if stressed else "calm",
                    }
                )
    overrides = [*skeleton["overrides"], *({k: v for k, v in g.items() if k != "regime"} for g in generated)]
    regimes = [[g["day"], g["regime"]] for g in generated]
    info: dict[str, Any] = {"version": gen_version, "seed_commitment": commitment(seed), "regimes": regimes}
    if scenario is not None:
        info["scenario"] = scenario
    return {**skeleton, "overrides": overrides, "macro": macro(seed, regimes, spec), "generator": info}


def macro(seed: str, regimes: list[list[Any]], spec: Spec) -> list[dict[str, Any]]:
    """As-of observations of the Street activity index for each generated day (``asof.Observation`` fields)."""
    rng = Stream(seed, MACRO_VERSION)
    out: list[dict[str, Any]] = []
    for day, regime in regimes:
        level = spec.macro_level + (spec.macro_regime if regime == "calm" else -spec.macro_regime)
        prints = [level + rng.integer(-spec.macro_first_noise, spec.macro_first_noise)]
        if rng.integer(0, 9_999) < spec.macro_revise_bp:
            prints.append(level + rng.integer(-spec.macro_revised_noise, spec.macro_revised_noise))
        for rev, tenths in enumerate(prints):
            out.append(
                {
                    "instrument": MACRO_SERIES,
                    "event_time": day,
                    "revision": rev,
                    "available_at": day + (spec.macro_revision_lag if rev else spec.macro_lag),
                    "value": str(tenths * TENTH),
                }
            )
    return out


def _scaled(v: str, pct: int, step: str) -> str:
    """``v`` scaled by pct percent, quantized to ``step`` (exact Decimal, HALF_EVEN)."""
    return str((Decimal(v) * pct / 100).quantize(Decimal(step), rounding=ROUND_HALF_EVEN))


def _terms(m: dict[str, Any]) -> str:
    """The margin notice's wording of a coefficient pair, e.g. ``initial 80/100%, maintenance 70/90%``."""
    pts = {k: {side: int(Decimal(m[k][side]) * 100) for side in ("long", "short")} for k in ("initial", "maintenance")}
    return (
        f"initial {pts['initial']['long']}/{pts['initial']['short']}%, "
        f"maintenance {pts['maintenance']['long']}/{pts['maintenance']['short']}%"
    )


def randomise(
    seed: str, gen_version: str, skeleton: dict[str, Any], spec: Spec
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The skeleton with its scenario parameters drawn from the seed; returns (skeleton, draws).

    Draws come from their own stream (``gen_version/scenario``), so the marks stream is independent.
    Public notices and the rally variant are rewritten to match, so every player-facing text
    still describes the tape. The recalled name is not randomised: ``balance.accept`` hardcodes BRIN.
    """
    rng = Stream(seed, f"{gen_version}/scenario")
    raw = copy.deepcopy(skeleton)
    shock = next(o for o in raw["overrides"] if o.get("headline_code") == "market_shock")
    d0 = shock["day"]
    d = d0 + rng.integer(-spec.crisis_days, spec.crisis_days)
    if d != d0 and any(o["day"] == d for o in raw["overrides"]):
        raise ValueError(f"crisis day {d} collides with an authored override")
    # the crisis day moves with its marks, volumes and any variant overrides
    for o in [*raw["overrides"], *(v for var in raw.get("variants", {}).values() for v in var["overrides"])]:
        if o["day"] == d0:
            o["day"] = d
    for var in raw.get("variants", {}).values():
        var["description"] = var["description"].replace(f"day {d0}", f"day {d}")
    # severity: a long and a short crisis mark, each moved within crisis_points
    marks = {s: Decimal(v) for s, v in shock["marks"].items()}
    long_base, short_base = min(marks.values()), max(marks.values())
    long_mark = long_base + rng.integer(-spec.crisis_points, spec.crisis_points)
    short_mark = short_base + rng.integer(-spec.crisis_points, spec.crisis_points)
    shock["marks"] = {s: str(long_mark if v == long_base else short_mark) for s, v in marks.items()}
    # stressed margin: both pairs move together, and the public notice is rewritten to match
    stressed = next(m for m in raw["margin_schedule"] if m["from_day"] == d0)
    old_terms = _terms(stressed)
    shift = Decimal(rng.integer(-spec.margin_points, spec.margin_points)) / 100
    for k in ("initial", "maintenance"):
        stressed[k] = {side: str(Decimal(v) + shift) for side, v in stressed[k].items()}
    stressed["from_day"] = d
    margin_notice = next(n for n in raw["public_notices"] if n.get("code") == "margin_terms")
    expected = f"{old_terms}) take effect day {d0}."
    if expected not in margin_notice["text"]:
        raise ValueError("margin_terms notice does not state the stressed terms")
    margin_notice["text"] = margin_notice["text"].replace(expected, f"{_terms(stressed)}) take effect day {d}.")
    # LP: the scheduled redemption and its notice, in 500-unit steps
    redemption_units = []
    for r in raw["redemptions"]:
        scaled = Decimal(r["units"]) * rng.integer(100 - spec.redemption_pct, 100 + spec.redemption_pct) / 100
        units = int((scaled / 500).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)) * 500
        article = "an" if units < 9000 or 11000 <= units < 12000 else "a"  # "an eight/eleven thousand"
        for n in raw["public_notices"]:
            if n.get("code") == "redemption_notice":
                n["text"] = n["text"].replace(f"a {int(Decimal(r['units'])):,}-unit", f"{article} {units:,}-unit")
        r["units"] = str(units)
        redemption_units.append(units)
    # rivals: every behavioural parameter scaled
    for f in raw["market"]["funds"]:
        f["params"] = {
            k: _scaled(v, rng.integer(100 - spec.rival_pct, 100 + spec.rival_pct), "0.0001")
            for k, v in f["params"].items()
        }
    # opening book: each position scaled; debt absorbs the market value change, so opening NAV is unchanged
    fund = raw["opening"]["fund"]
    mark = Decimal(raw["defaults"]["mark"])
    debt = Decimal(fund["debt"])
    for s, q in fund["positions"].items():
        pct = rng.integer(100 - spec.book_pct, 100 + spec.book_pct)
        new = int((Decimal(q) * pct / 100 / 100).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)) * 100
        debt += (new - q) * mark
        fund["positions"][s] = new
    fund["debt"] = str(debt)
    draws = {
        "crisis_day": d,
        "crisis_long_mark": str(long_mark),
        "crisis_short_mark": str(short_mark),
        "margin_shift": str(shift),
        "redemption_units": redemption_units,
        "opening_debt": fund["debt"],
    }
    return raw, draws


def family_of(seed: str) -> str:
    """Seeds written ``family#n`` share a family; any other seed is its own family."""
    return seed.split("#", 1)[0]


def split_of(seed: str) -> Literal["train", "val", "test"]:
    """Deterministic 80/10/10 split by seed family, so whole families are held out together.

    Same hash and salt as the ML package's ``contracts.split_of``: for a family string both return the same split.
    """
    family = family_of(seed)
    if not family:
        raise ValueError("seed family must be non-empty")
    bucket = int.from_bytes(hashlib.sha256(f"{SPLIT_SALT}|{family}".encode()).digest()[:8], "big") % 10
    return "test" if bucket == 9 else "val" if bucket == 8 else "train"

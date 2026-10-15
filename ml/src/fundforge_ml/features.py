"""Offline point-in-time seat features in Polars, byte-identical to the live ``stream`` fold.

``point_in_time(events, cutoffs)`` answers, for every cutoff row ``(room_id, seat, step, as_of_seq,
as_of_day, as_of_phase)``, "what would ``stream.features`` have said for this seat at that moment?".
An event counts only if it is available at the cutoff: ``seq <= as_of_seq`` (it was committed
before the decision) **and** its simulated ``(day, phase)`` is not after the cutoff's. Visibility
is the stream's: ``public`` plus the seat's own audience, deduplicated by ``event_id``; ``internal``
rows and other rooms never count. The ``features`` column is ``canonical(snapshot)``; the parity
tests compare it byte for byte with ``canonical(stream.features(...)[seat])``.

Events are flattened in Python (one dict lookup per field, plus the stream's hidden-truth refusal);
filtering, deduplication and every aggregate run in Polars.
"""

import json
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

import polars as pl

from .contracts import hidden_paths
from .stream import FEATURE_VERSION, PHASES, normalize

KEY = ["room_id", "seat", "step"]
CUTOFF_SCHEMA = {
    "room_id": pl.String,
    "seat": pl.String,
    "step": pl.Int64,
    "as_of_seq": pl.Int64,
    "as_of_day": pl.Int64,
    "as_of_phase": pl.String,
}
EVENT_SCHEMA = {
    "room_id": pl.String,
    "event_id": pl.String,
    "seq": pl.Int64,
    "audience": pl.String,
    "kind": pl.String,
    "day": pl.Int64,
    "ph": pl.Int64,
    "role": pl.String,
    "code": pl.String,
    "deficit": pl.String,
    "topic": pl.String,
    "label": pl.String,
}
DEC = pl.Decimal(38, 12)  # ordering only; the reported value is the event's own decimal string


def canonical(snapshot: Mapping[str, Any]) -> str:
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))


def flatten(events: Iterable[Mapping[str, Any]]) -> pl.DataFrame:
    """Outbox rows (Store rows or Debezium messages) to one typed row per event."""
    out = []
    for raw in events:
        ev = normalize(raw)
        p = ev["payload"]
        if ev["audience"] != "internal" and ev["kind"] != "outcome" and list(hidden_paths(p)):
            raise ValueError(f"hidden truth in a live event {ev['event_id']}")
        refs = p.get("refs") or {}
        is_notice = ev["kind"] == "notice"
        out.append(
            {
                "room_id": ev["room_id"],
                "event_id": ev["event_id"],
                "seq": int(ev["seq"]),
                "audience": ev["audience"],
                "kind": ev["kind"],
                "day": int(ev["day"]),
                "ph": PHASES.index(ev["phase"]),
                "role": p.get("role") if ev["kind"] == "command" else None,
                "code": p.get("code") if ev["kind"] in ("notice", "incident") else None,
                "deficit": refs.get("deficit") if is_notice and p.get("code") == "margin_call" else None,
                "topic": refs.get("topic") if is_notice and p.get("code") == "research_reveal" else None,
                "label": p.get("label") if ev["kind"] == "outcome" else None,
            }
        )
    return pl.DataFrame(out, schema=EVENT_SCHEMA)


def _counts(visible: pl.DataFrame, kind: str, col: str, name: str) -> pl.DataFrame:
    return (
        visible.filter(pl.col("kind") == kind)
        .group_by([*KEY, col])
        .len()
        .group_by(KEY)
        .agg(pl.struct(pl.col(col).alias("k"), pl.col("len").alias("v")).alias(name))
    )


def point_in_time(events: pl.DataFrame, cutoffs: pl.DataFrame) -> pl.DataFrame:
    """One row per cutoff: KEY, as-of columns and the canonical feature JSON."""
    cut = cutoffs.with_columns(
        as_of_ph=pl.col("as_of_phase").replace_strict(list(PHASES), list(range(len(PHASES))), return_dtype=pl.Int64)
    )
    t = pl.col("day") * 10 + pl.col("ph")
    visible = (
        cut.join(events, on="room_id")
        .filter(
            (pl.col("audience") == "public") | (pl.col("audience") == pl.col("seat")),
            pl.col("seq") <= pl.col("as_of_seq"),  # available_at <= t: committed before the cutoff
            t <= pl.col("as_of_day") * 10 + pl.col("as_of_ph"),
        )  # ... and not later in sim time
        .unique([*KEY, "event_id"], keep="any")
    )
    notices = pl.col("kind") == "notice"
    base = visible.group_by(KEY).agg(
        events=pl.len(),
        wm=t.max(),
        deficit=pl.col("deficit").filter(notices).sort_by(pl.col("deficit").filter(notices).cast(DEC)).last(),
        research=pl.col("topic").filter(notices).drop_nulls().unique().sort(),
        outcome=pl.col("label").filter(pl.col("kind") == "outcome").first(),
    )
    table = cut.join(base, on=KEY, how="left")
    for kind, col, name in (
        ("command", "role", "commands"),
        ("notice", "code", "notices"),
        ("incident", "code", "incidents"),
    ):
        table = table.join(_counts(visible, kind, col, name), on=KEY, how="left")
    rows = [
        {**{k: r[k] for k in CUTOFF_SCHEMA}, "features": canonical(_snapshot(r))}
        for r in table.sort(KEY).iter_rows(named=True)
    ]
    return pl.DataFrame(rows, schema={**CUTOFF_SCHEMA, "features": pl.String})


def _snapshot(r: Mapping[str, Any]) -> dict[str, Any]:
    """The same dict as ``stream.SeatFeatures.snapshot``."""

    def counter(items: list[dict[str, Any]] | None) -> dict[str, int]:
        return dict(sorted((x["k"], x["v"]) for x in items or []))

    wm = r["wm"]
    deficit = r["deficit"]
    if deficit is None or Decimal(deficit) <= 0:  # the stream starts from Decimal(0) and takes the max
        deficit = "0"
    return {
        "room_id": r["room_id"],
        "seat": r["seat"],
        "events": r["events"] or 0,
        "commands_by_role": counter(r["commands"]),
        "notices_by_code": counter(r["notices"]),
        "incidents_by_code": counter(r["incidents"]),
        "watermark": [0, -1] if wm is None else [wm // 10, wm % 10],
        "max_margin_deficit": deficit,
        "research_revealed": list(r["research"] or []),
        "outcome_label": r["outcome"],
        "version": FEATURE_VERSION,
    }


def at_end(events: pl.DataFrame, room_id: str, seats: Iterable[str]) -> pl.DataFrame:
    """Cutoffs after the last event of a room (used to compare with a whole-stream fold)."""
    mine = events.filter(pl.col("room_id") == room_id)
    last = mine.sort(["day", "ph"]).tail(1)
    day, ph = (last["day"][0], last["ph"][0]) if len(last) else (0, 0)
    seq = int(mine["seq"].max() or 0)  # type: ignore[arg-type]
    return pl.DataFrame(
        [
            {"room_id": room_id, "seat": s, "step": -1, "as_of_seq": seq, "as_of_day": day, "as_of_phase": PHASES[ph]}
            for s in seats
        ],
        schema=CUTOFF_SCHEMA,
    )

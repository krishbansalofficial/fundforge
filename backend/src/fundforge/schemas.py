"""Wire contract of the player-facing HTTP responses, for the OpenAPI schema and generated client types.

``Session.view`` and the API still build plain dicts; these models describe them. They forbid extra
fields, and ``test_schemas.py`` validates real views from whole games against them, so a field added to
a view without updating this contract fails a test instead of silently reaching clients untyped.
Money, prices, units and ratios are decimal strings exactly as the server formats them; never parse
them into binary floats for arithmetic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Dec = str  # a decimal number serialized as a string


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NextEvent(Strict):
    day: int
    phase: str
    date: str


class Clock(Strict):
    day: int
    date: str
    phase: str
    next: NextEvent | None
    finished: bool


class ClockState(Strict):
    speed: int
    paused: bool
    reason: str | None


class Chat(Strict):
    day: int
    phase: str
    role: str
    text: str
    ref: Any = None


class Fund(Strict):
    nav: Dec
    cash: Dec
    collateral: Dec
    debt: Dec
    credit_left: Dec
    reserve: Dec
    long_mv: Dec
    short_mv: Dec
    gross: Dec | None
    net: Dec | None
    maintenance_req: Dec
    initial_req: Dec
    margin_call: Dec | None


class Position(Strict):
    sym: str
    qty: int
    mark: Dec
    mv: Dec
    borrowed: int


class Series(Strict):
    id: str
    units: Dec
    net: Dec
    provision: Dec
    hwm: Dec
    nav_per_unit: Dec


class Firm(Strict):
    cash: Dec
    fee_receivable: Dec
    payroll_payable: Dec


class Recall(Strict):
    open: int
    resolved_by: str | None
    offer_visible: bool
    replacement_accepted: bool


class Notice(Strict):
    """A typed event; ``text`` is rendered prose, ``code``/``refs`` are what logic should read."""
    code: str
    day: int
    date: str
    phase: str
    kind: str
    refs: dict[str, str | int]
    text: str


class ResearchUse(Strict):
    topic: str
    assigned_day: int
    reveal_day: int
    owner: str | None = None


class Assignment(Strict):
    role: str
    location: str


class Research(Strict):
    used: list[ResearchUse]
    budget: int
    shared: list[str]
    evidence: list[Notice]
    topics: list[str]
    assignments: dict[str, Assignment]


class AttentionClaim(Strict):
    window: int
    location: str
    assignment: str


class Attention(Strict):
    window: int
    committed: bool
    partners: dict[str, AttentionClaim]


class Fill(Strict):
    day: int
    phase: str
    qty: int
    price: Dec
    amount: Dec


class RejectedFill(Strict):
    day: int
    phase: str
    rejected: str


class Order(Strict):
    order_id: str
    sym: str
    side: str
    qty: int
    filled: int
    status: str
    forced: str | None
    fills: list[Fill | RejectedFill]


class PackageOrder(Strict):
    order_id: str
    sym: str
    side: str
    qty: int
    limit: Dec | None


class Package(Strict):
    package_id: str
    proposer: str
    digest: str
    status: str
    signatures: list[str]
    orders: list[PackageOrder]


class LeagueRow(Strict):
    id: str
    name: str
    style: str
    status: str
    return_bps: Dec
    nav: Dec


class IncidentEvent(Strict):
    code: str
    day: int
    phase: str
    refs: dict[str, str | int]
    amounts: dict[str, Dec]
    text: str


class Decision(Strict):
    day: int
    phase: str
    role: str
    type: str
    detail: dict[str, Any]


class Outcome(Strict):
    label: Literal["WIN", "SURVIVAL", "DISTRESS"]
    nav: Dec
    fund_return_bps: Dec
    benchmark_return_bps: Dec
    excess_bps: Dec
    score: Dec
    rank: int
    funds: int
    redemption_paid: Dec
    forced: list[str]
    unpaid: list[str]
    recall_resolved_by: str | None
    variant: str
    journal_digest: str
    tape_digest: str


class Realtime(Strict):
    running: bool
    speed: int
    next_tick_at: str | None
    server_now: str
    next_tick_in: float
    window_seconds: float


class SessionView(Strict):
    """``Session.view``: everything one partner may see at one room version."""
    role: str
    partners: dict[str, str]
    clock: Clock
    ready: list[str]
    clock_state: ClockState
    bots: list[str]
    chat: list[Chat]
    version: int
    fund: Fund
    positions: list[Position]
    marks: dict[str, Dec]
    series: list[Series]
    firm: Firm
    recall: Recall
    research: Research
    attention: Attention
    orders: list[Order]
    packages: list[Package]
    notices: list[Notice]
    league: list[LeagueRow]
    incidents: list[str]
    incident_events: list[IncidentEvent]
    decisions: list[Decision]
    outcome: Outcome | None


class RoomView(SessionView):
    """``GET /api/rooms/{id}/view``: the session view plus seat names and the real-time clock."""
    names: dict[str, str]
    realtime: Realtime


class JournalEntry(Strict):
    id: str
    entity: str
    date: str
    memo: str
    postings: list[tuple[str, Dec]]


class LedgerPage(Strict):
    """``GET /api/rooms/{id}/ledger``: entries ``next - len(entries)`` up to ``next`` of one entity's journal."""
    entity: Literal["fund", "firm"]
    entries: list[JournalEntry]
    next: int
    digest: str


class NewRoomResponse(Strict):
    room_id: str
    tokens: dict[str, str]
    names: dict[str, str]
    bot_role: str | None

"""Wire contract of the player-facing HTTP responses, for the OpenAPI schema and generated client types.

``Session.view`` and the API still build plain dicts; these models describe them. They forbid extra
fields, and ``test_schemas.py`` validates real views from whole games against them, so a field added to
a view without updating this contract fails a test instead of silently reaching clients untyped.
Money, prices, units and ratios are decimal strings exactly as the server formats them; never parse
them into binary floats for arithmetic.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, RootModel, StringConstraints

Dec = str  # a decimal number serialized as a string
# Stricter form used by the terminal and debrief contracts: plain digits, never an exponent or a JSON number.
DecOut = Annotated[str, StringConstraints(pattern=r"^-?\d+(\.\d+)?$")]
Band = Literal["strong", "stable", "concerned", "withdrawal_risk"]


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
    kind: Literal["orders", "gate"]
    terms: dict[str, Any]  # a gate binds {"deal_day", "requests": {series: units}}; empty for orders


class LpRow(Strict):
    id: str
    band: Literal["strong", "stable", "concerned", "withdrawal_risk"]  # from the last certified checkpoint
    requested_units: Dec | None
    carried_units: Dec | None
    first_cutoff: int
    contacted: bool


class Investors(Strict):
    """The managing partner's LP inbox in generated rooms; exact confidence stays server-side until the debrief."""
    policy: str
    deal_day: int | None
    gate_elected: bool
    lps: list[LpRow]


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
    lp_deferred: dict[str, Dec] | None = None  # generated rooms: gated units carried past the end
    scenario: str
    max_drawdown: DecOut  # peak-to-trough fall of fund NAV per unit over business closes, a 6dp fraction
    # generated rooms, finished runs only: never in any view before the end
    seed_commitment: str | None = None
    stressed_days: int | None = None
    generated_days: int | None = None


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
    investors: Investors | None  # managing partner only, generated rooms only


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


# ---------- terminal (GET /api/rooms/{id}/terminal) ----------

class AsOf(Strict):
    event: int
    day: int
    date: str
    phase: str


class Quote(Strict):
    sym: str
    mark: DecOut
    qty: int
    mv: DecOut
    change_bps: DecOut | None
    since_start_bps: DecOut | None
    weight: DecOut | None
    borrowed: int
    borrow_rate: DecOut | None
    observed_event_volume: int | None  # the authored capacity of the last processed event, not traded volume


class HistoryPoint(Strict):
    event: int
    day: int
    date: str
    phase: str
    marks: dict[str, DecOut]


class Break(Strict):
    """A control discrepancy; ``actual``/``expected`` are diagnostic text, not always numbers."""
    code: str
    subject: str
    actual: str | None = None
    expected: str | None = None


class AdminSeries(Strict):
    series_id: str
    units: DecOut
    hwm: DecOut
    net: DecOut
    provision: DecOut


class AdminClaim(Strict):
    date: str
    series_id: str
    units: DecOut
    price: DecOut
    payable: DecOut
    crystallized_fee: DecOut


class AdministratorReport(Strict):
    status: Literal["checked", "break"]
    breaks: list[Break]
    close_count: int
    claim_count: int
    series: list[AdminSeries]
    liabilities: dict[str, DecOut]
    claims: list[AdminClaim]


class Settlement(Strict):
    obligation: str
    kind: str
    sym: str
    qty: int
    amount: DecOut
    due_day: int
    status: Literal["pending", "settled"]
    failed_days: list[int]


class Coordinate(Strict):
    day: int
    phase: str


class StatementRevision(Strict):
    id: str
    revision: int
    source: str
    account: str
    as_of: Coordinate
    available_at: Coordinate
    balance: DecOut
    expected: DecOut
    received_date: str
    supersedes: int | None
    reason: str


class StatementResolution(Strict):
    statement_id: str
    revision: int
    date: str
    actor: str


class StatementRow(Strict):
    id: str
    owner: str
    status: Literal["open", "resolved"]
    age_calendar_days: int
    revision: int
    account: str
    actual: DecOut
    expected: DecOut
    can_resolve: bool
    resolution: StatementResolution | None
    resolution_history: list[StatementResolution]
    history: list[StatementRevision]


class BrokerSummary(Strict):
    activity_count: int
    fee_line_count: int
    statement_count: int
    balances: dict[str, DecOut]
    financing_accrued: DecOut
    financing_invoiced: DecOut


class ControlReport(Strict):
    """``Engine.control_report``: scoped reconciliation, not external NAV certification (see ``scope``)."""
    status: Literal["checked", "break"]
    execution_status: Literal["checked", "break"]
    breaks: list[Break]
    confirmations: int
    expected_positions: dict[str, int]
    conditional_nav: DecOut
    book_nav: DecOut
    scope: str
    administrator: AdministratorReport
    settlements: list[Settlement]
    statement_queue: list[StatementRow]
    broker: BrokerSummary


class Stress(Strict):
    id: str
    label: str
    long_shock: DecOut
    short_shock: DecOut
    pnl: DecOut
    nav: DecOut
    maintenance_req: DecOut
    headroom: DecOut
    margin_breach: bool
    gross: DecOut | None


class TerminalRisk(Strict):
    controls: ControlReport
    nav: DecOut
    long_mv: DecOut
    short_mv: DecOut
    maintenance_req: DecOut
    headroom: DecOut
    cash: DecOut
    restricted_collateral: DecOut
    debt: DecOut
    credit_left: DecOut
    maintenance_rates: dict[str, DecOut]
    stress_method: str
    stresses: list[Stress]


class NewsItem(Notice):
    visibility: Literal["private", "shared"]


class TerminalOrder(Strict):
    order_id: str
    sym: str
    side: str
    qty: int
    filled: int
    remaining: int
    status: str
    forced: str | None
    fills: list[Fill | RejectedFill]


class MacroPrint(Strict):
    """One published print of a generated market's indicator; a later revision appears only from its own day."""
    series: str
    period_day: int
    published_day: int
    revision: int
    value: DecOut


class RegimeQuestion(Strict):
    question: str  # e.g. "regime:12"; the ``thesis`` command answers it
    period_day: int
    states: list[Literal["calm", "stressed"]]
    prior: Forecast
    posterior: Forecast
    evidence: int
    method: str


class TerminalView(Strict):
    """``GET /api/rooms/{id}/terminal``: read-only as-of analytics at one room version."""
    schema_: Literal["forge-terminal-v1"] = Field(alias="schema")
    finished: bool
    role: str | None
    as_of: AsOf
    source: str
    quotes: list[Quote]
    history: list[HistoryPoint]
    history_truncated: bool
    risk: TerminalRisk
    news: list[NewsItem]
    incidents: list[IncidentEvent]
    orders: list[TerminalOrder]
    league: list[LeagueRow]
    macro: list[MacroPrint]  # empty in authored markets
    regime: RegimeQuestion | None  # generated markets only
    version: int


# ---------- debrief (POST /api/rooms/{id}/debrief) ----------

class BranchState(Strict):
    day: int
    phase: str
    nav: DecOut
    headroom: DecOut
    recall_open: int
    positions: dict[str, int]
    journal_digest: str


class TimelineStep(Strict):
    seq: int
    role: str
    type: str
    status: Literal["accepted", "rejected", "omitted"]
    before: BranchState
    after: BranchState
    nav_delta: DecOut | None = None  # absent on the omitted step
    can_omit: bool | None = None


class RejectedStep(Strict):
    seq: int
    type: str
    reason: str


class ThesisScore(Strict):
    role: str
    question: str
    period_day: int
    recorded_day: int
    forecast: Forecast
    true_regime: Literal["calm", "stressed"]
    brier: DecOut


class SeatResearch(Strict):
    theses: int
    mean_brier: DecOut | None


class ResearchRecord(Strict):
    """Brier scores of each seat's latest thesis per question; beside P&L, never in it."""
    theses: list[ThesisScore]
    seats: dict[str, SeatResearch]
    policy: str


class ReviewCheckpoint(Strict):
    day: str
    kind: Literal["review"]
    lp: str
    policy_version: str
    start: DecOut
    drawdown: DecOut
    response_lag: DecOut
    contact: DecOut
    clamp: DecOut
    end: DecOut
    band: Band
    drawdown_pp: DecOut
    open_alerts: DecOut


class ChapterCheckpoint(Strict):
    day: str
    kind: Literal["chapter_close"]
    lp: str
    policy_version: str
    start: DecOut
    performance: DecOut
    breaches: DecOut
    report: DecOut
    meeting: DecOut
    gate: DecOut
    herding: DecOut
    overdue: DecOut
    clamp: DecOut
    end: DecOut
    band: Band


class LpFinal(Strict):
    confidence: DecOut
    band: Band


class LpDebrief(Strict):
    """Generated rooms: every LP confidence component, revealed only after the run."""
    policy: str
    checkpoints: list[Annotated[ReviewCheckpoint | ChapterCheckpoint, Field(discriminator="kind")]]
    final: dict[str, LpFinal]
    carried_units: dict[str, DecOut]


class BranchOutcome(Outcome):
    """A counterfactual branch may stop before the end; it is then not a comparable ending score."""
    label: Literal["WIN", "SURVIVAL", "DISTRESS", "IN_PROGRESS"]  # type: ignore[assignment]


class Debrief(Strict):
    """``POST /api/rooms/{id}/debrief``: completed-run causal replay, optionally omitting one decision."""
    branch_id: str
    source_version: int
    rules_version: str
    tape_digest: str
    omitted_seq: int | None
    finished: bool
    state: BranchState
    outcome: BranchOutcome
    source_outcome: Outcome
    nav_difference: DecOut
    research: ResearchRecord
    investors: LpDebrief | None = None  # present in generated rooms only
    timeline: list[TimelineStep]
    rejected: list[RejectedStep]
    incidents: list[IncidentEvent]
    policy: str


# ---------- commands (POST /api/rooms/{id}/commands) ----------
# Shapes only. Whether a command is allowed (role, limits, deadlines, mandate) stays with the versioned rules
# in governance/engine. Decimal inputs must be plain decimal strings, never JSON numbers, so money never
# passes through a binary float; integers accept whole JSON numbers (Godot parses every number as a float).

DECIMAL_PATTERN = r"^-?\d{1,15}(\.\d{1,6})?$"
DecIn = Annotated[str, StringConstraints(pattern=DECIMAL_PATTERN)]
Id = Annotated[str, StringConstraints(min_length=1, max_length=100)]
Side = Literal["BUY", "SELL", "SHORT", "COVER"]


class OrderSpec(Strict):
    order_id: Id
    sym: Id
    side: Side
    qty: int
    limit: DecIn | None = None


class Ticket(OrderSpec):
    type: Literal["ticket"]


class Propose(Strict):
    type: Literal["propose"]
    package_id: Id
    orders: list[OrderSpec] = Field(max_length=50)
    source_version: int | None = None


class Sign(Strict):
    type: Literal["sign"]
    package_id: Id
    digest: Id


class Cancel(Strict):
    type: Literal["cancel"]
    order_id: Id


class ResearchCommand(Strict):
    """Legacy engine-script assignment; players use ``visit``."""
    type: Literal["research"]
    topic: Id


class Visit(Strict):
    type: Literal["visit"]
    location: Id
    assignment: Id


class ShareResearch(Strict):
    type: Literal["share_research"]
    topic: Id


class AcceptReplacement(Strict):
    type: Literal["accept_replacement"]


class SetReserve(Strict):
    type: Literal["set_reserve"]
    amount: DecIn


class ResolveStatement(Strict):
    type: Literal["resolve_statement"]
    statement_id: Id
    revision: int
    version: int


class Ready(Strict):
    type: Literal["ready"]
    version: int | None = None  # the room version the partner reviewed; clients should always send it
    skip: bool = False


class SetSpeed(Strict):
    type: Literal["set_speed"]
    speed: int


class Say(Strict):
    type: Literal["say"]
    text: Annotated[str, StringConstraints(max_length=240)]
    ref: Id | None = None  # what the message is about, e.g. the bot's "research:borrow"


class Pause(Strict):
    type: Literal["pause"]


class Forecast(Strict):
    calm: DecIn
    stressed: DecIn


class Thesis(Strict):
    """A seat's forecast for the terminal's live regime question; scored in the debrief, never in P&L."""
    type: Literal["thesis"]
    question: Id  # e.g. "regime:12", the terminal's ``regime.question``
    forecast: Forecast  # probabilities summing to exactly 1


class ContactLp(Strict):
    """Managing partner: spend this window's attention on one LP before its next review (generated rooms)."""
    type: Literal["contact_lp"]
    lp: Id


class ProposeGate(Strict):
    """Propose a redemption gate for the next dealing close; the other partner elects it with ``sign``."""
    type: Literal["propose_gate"]
    package_id: Id


# ``tick`` is not here: only the server's clock issues it, never an HTTP client.
Command = Annotated[
    Ticket | Propose | Sign | Cancel | ResearchCommand | Visit | ShareResearch | AcceptReplacement | SetReserve
    | ResolveStatement | Ready | SetSpeed | Say | Pause | Thesis | ContactLp | ProposeGate,
    Field(discriminator="type"),
]


class CommandBody(RootModel[Command]):
    """The request body. A root model keeps the ``type`` discriminator, which FastAPI's ``Body()`` would drop."""


COMMAND_TAGS = {get_args(m.model_fields["type"].annotation)[0] for m in get_args(get_args(Command)[0])}

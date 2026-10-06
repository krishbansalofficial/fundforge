# OpenSEO: repository assessment and bounded integration

Design version 2.0, 6 October 2026. Assumed target: [every-app/open-seo](https://github.com/every-app/open-seo), the upstream of the similarly named afazhriel/openseo fork. The user supplied a name rather than a URL; confirm a different target if intended. This assessment does not silently substitute OpenBB. No upstream source has been copied, installed, deployed, or connected to a paid account.

## What was actually inspected

Pinned source snapshot: `ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6`, retrieved through GitHub. The README describes SEO workflows and a DataForSEO-backed service. The LICENSE is MIT, copyright 2026 Ben Senescu. The dependency manifest shows a TypeScript/React/TanStack/Cloudflare stack, unlike FundForge's planned Python financial domain. Read these pinned files before reuse:

| Inspected path | Relevant observation | FundForge decision |
|---|---|---|
| `src/server/mcp/tools/get-domain-overview.ts` | Structured domain metrics and project-scoped handler | Optional research source, not price feed |
| `src/server/mcp/tools/research-keywords.ts` | Bounded seeds, partial results, market context, estimated volumes | Evidence cards must preserve scope and missingness |
| `src/server/lib/dataforseo/core.ts` | Timeouts, error classification, bounded retries, explicit non-idempotent exception | Adopt the design principle; implement in our adapter |
| `src/server/lib/dataforseo/client.ts` | Provider/service integration with billing dependencies | Do not transplant the whole client |
| `src/server/mcp/project-auth.ts` | Resource membership checks | Apply our own fund authorization at every boundary |
| `src/server/lib/r2-cache.ts` | Parameter-based cache keys, TTL and validation caution | Extend keys with information cutoff and dataset version |
| `package.json`, `LICENSE` | Stack and source license | No wholesale fork or forced stack migration |

These are source observations, not a security audit or performance certification. Source license and underlying data rights are separate. Preserve the MIT notice if substantial code is later copied; add exact paths, snapshot, modifications, and dependencies to a third-party notice. Validate provider retention/display/export rights before incorporating real data. Current pricing and API behavior must be checked when enabling a provider; this plan authorizes no charges.

## The valuable game feature: alternative-data research desk

Make information acquisition a strategic choice. A consumer-company analyst can compare search interest for a brand, a competitor, and a product category, investigate conflicting signals, and write a falsifiable thesis. The player spends fictional analyst capacity on a question, receives a timestamped evidence card, then decides whether it changes an existing position. The same action can use an authored fixture in campaign mode or an entitled adapter in a later sandbox.

Example: search interest for a fictional retailer rises, but a second report attributes it to product recalls. Buying the first bullish narrative without triangulation is a bad process; it must not be mechanically guaranteed to lose money. Evidence influences the player's judgment, not an automatic price multiplier or a hidden correctness grade.

Proposed research products:

| Product | Decision it supports | Required caveat |
|---|---|---|
| Brand/category search-interest comparison | Demand thesis, competitor substitution | Estimated search activity is not sales or unique customers |
| Domain visibility report | Distribution/customer acquisition thesis | SEO rank/estimated organic traffic is not audited revenue |
| Competitor evidence packet | Choose what to investigate next | Domain-to-listed-company relationship must be curated and dated |
| Source disagreement card | Decide to wait, size smaller, or buy another report | Conflicting proxies can remain unresolved |

Do not sum search volumes for close variants, infer stock prices from SEO values, or pretend historical monthly estimates were available daily. CPC is an advertising metric, not a security valuation. Today's provider retrieval does not establish what was knowable in an earlier season. Company-owned GA/Search Console integrations cannot provide competitors' private analytics; exclude those from the base design.

## Integration boundary

Preferred initial approach: no runtime dependency. Author synthetic research packets against a provider-neutral schema. Later, run OpenSEO separately and access an explicitly allowlisted research interface through a server adapter, or implement a small direct provider adapter if maintaining a second application is unjustified. Compare those alternatives in a bounded spike before choosing. Keep the engine and campaign usable when either fails.

Pipeline: operator-authorized fetch → normalized observation → provenance/rights checks → immutable approved dataset → as-of information service → player evidence card. A historical campaign consumes only the approved dataset. Never fetch current external results during a historical decision and backdate them.

`ResearchObservation` contract:

```json
{
  "id": "obs-example-001",
  "entity_id": "fictional-retailer-a",
  "metric": "brand_search_volume_estimate",
  "value": "12000",
  "unit": "estimated_searches_per_month",
  "geography": "US",
  "language": "en",
  "period_start": "2026-01-01",
  "period_end": "2026-01-31",
  "source_published_at": null,
  "observed_at": "2026-02-05T12:00:00Z",
  "available_at": "2026-02-05T12:00:00Z",
  "provider": "synthetic_fixture",
  "dataset_version": "research-demo-v1",
  "revision": 1,
  "mapping_version": "entities-v1",
  "quality_flags": ["estimate", "not_revenue"],
  "license_ref": "authored-fixture",
  "synthetic": true
}
```

In real snapshots, conservatively set `available_at` no earlier than collection unless independently evidenced historical publication supports earlier availability. Null timestamps must never mean unlimited visibility. Retain revisions; do not overwrite old observations. Store a raw-source hash only where retention rights permit it. Validate entity, unit, geography, period and missing values before import. Campaign fixture times use the scenario's declared clock mapping rather than an implicit wall-clock comparison.

The fetch worker uses a service credential scoped to the research project. Players cannot supply arbitrary target URLs or access another fund's snapshots. Allowlisted domains and bounded sizes prevent research requests becoming arbitrary network fetches. Provider text is untrusted; it cannot approve orders, alter mandates, run code, or become privileged instructions.

## Budget and failure contracts

There are two separate budgets: fictional research actions inside the game, and real provider/model usage. Spending fictional credits never authorizes a paid API request. Real usage defaults to disabled, with an operator-configured currency ceiling and request cap before activation. Record estimated/reserved/actual/unknown charge states. A timeout on a chargeable request may already have incurred a charge; do not automatically retry without provider-supported reconciliation or idempotency.

Cache keys include provider, endpoint, normalized parameters, entitlement scope, dataset/revision, and historical cutoff. An expired cache is either visibly stale in the research sandbox or unavailable; it cannot silently refresh a locked campaign. Errors distinguish unavailable, stale, forbidden, budget exhausted, and malformed response. No fabricated zeroes. The game continues with its approved fixture or existing observations, with provenance unchanged.

## What not to inherit

Do not reuse OpenSEO's billing account as virtual fund accounting, its project membership as investment authority, or its crawler as a general unrestricted research agent. Do not import its full SaaS, marketing, Cloudflare deployment, telemetry, or authentication stack just to display three research metrics. It does not supply exchange execution, stock borrow, fund NAV, capital accounts, LP contracts, a deterministic simulation clock, or a game economy.

OpenSEO can also help discover search terms and audit a future public FundForge marketing site. That is separate from gameplay and is out of the present implementation scope.

## Go/no-go spike and evidence

After the core game gate, spend one bounded task on: a saved fixture → normalized observation → as-of card; source inspection of the chosen API; rights/credentials/cost decision; one adapter contract test for malformed/partial/error responses; and a dependency/spend comparison of separate OpenSEO versus direct provider adapter. Stop if no valid historical data or useful player decision results. The fixture feature remains valuable without a live connection.

Success is improved research decisions in a blind playtest and correct information cutoffs, not a claim that SEO predicts returns. Any ML experiment needs point-in-time snapshots, an ablation against price-only/fundamental baselines, entity-held-out or chronological evaluation as appropriate, and costs. No claimed alpha until measured honestly.

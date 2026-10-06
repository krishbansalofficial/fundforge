# Decision log

These are selected specification defaults, not verified implementation decisions. Change only with a concrete reason and identify impacted tests/season comparability.

| Decision | Default | Reason |
|---|---|---|
| Product boundary | Virtual-money cooperative educational game | Realistic learning without implementing real pooled capital |
| Capital sharing | Equal units; no in-season flows in V1 | Clear symmetric sharing of gains and losses |
| Architecture | Modular FastAPI + PostgreSQL; Next.js UI | One transaction authority, reusable Python finance core |
| V1 order model | Whole-share long-only market orders at next open | Avoids daily-bar intraday fill invention and known-close fills |
| V1 account policy | Settled cash only, no sale of unsettled buys | Conservative teachable commitment/settlement behavior |
| Concurrency | Fund lock, DB uniqueness, request/event dedupe | Protect combined cash/exposure and economic identity |
| User presence | Two actual managers; no AI substitutes for human approval | Preserves cooperation and authority |
| UI budget | Five readable screens, modest components | Gameplay clarity with limited build effort |
| Initial data | Deterministic synthetic fixtures | No credential/spend dependency for first playable slice |
| Data-dependent scope | Licensed adapter only after rights/availability check | Display rights and historical provenance matter |
| ML first candidate | Baseline versus filtered HMM; daily batch inference | Reuses knowledge while proving lifecycle/evaluation |
| AI tutor | Templates first, optional bounded API | Core works without external spend or hallucinated arithmetic |
| Development agents | One builder, optional one bounded reviewer | Evidence-based review with controlled context growth |
| Advanced features | Separate gates/extensions | Mechanics require dedicated accounting/data tests |

## Open decisions at first inspection

- Runtime/dependency versions and package managers compatible with the actual environment.
- Auth provider and same-origin cookie/BFF versus verified bearer-token architecture.
- Actual installed Vercel skill names and selected task routing.
- Market-data provider, entitlements, coverage/rights and historical settlement/calendar source.
- Approved universe and initial fixture/scenario format extension.
- Deployment provider, credentials, budget and private access when requested.
- ML target/evaluation objective and final held-out period based on available data.

## Record a resolved decision

Date / task ID / decision / evidence / alternatives actually considered / consequences / affected tests and datasets / owner. Do not restate all previous decisions after each task.

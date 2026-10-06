# Recruiter and interview evidence

This project becomes persuasive through implemented evidence. It is not a hiring guarantee, a replacement for fundamentals/interview practice, or evidence of an actual hedge fund.

## Backend story

Two collaborating managers can send competing requests and retry them across unreliable networks, while portfolio state remains correct. Show the DB transaction/lock boundary, exact idempotency identity, proposal version binding, reservations, settlement journal, reconciliation and recovery. Explain why PostgreSQL owns state, how outbox delivery avoids lost notifications, and why WebSocket/Redis loss does not change balances.

Artifacts to retain: architecture/decision diagram after implementation; threat model with reproduced abuse cases; database transaction tests; fixture replay; crash-recovery trace; backup restore; load report with hardware and operation mix; short demo of two identities. Do not claim distributed scale solely because Redis or Docker is present.

## ML-engineering story

A versioned point-in-time feature pipeline evaluates a candidate against a simpler baseline, deploys only a justified artifact, and exposes versioned as-of predictions with monitoring/fallback. Show the chronological split, leakage test, rejected candidates, actual experiment table and release manifest. Explain filtered HMM inference versus smoothing and the limits of unsupervised regime labels.

Artifacts to retain: frozen dataset/config/checksum; feature schema; folds and final holdout; cost sensitivity; model registry/release record; serving/fallback demonstration; drift/failure report; explanation evaluation. A candidate losing to a baseline is credible if the evaluation is sound.

## Resume bullets — templates, not completed claims

Use only after implementation. Replace every bracket with a measured fact; remove claims whose evidence is missing.

- Preserved [ledger/portfolio invariant] across [N tested concurrent operations and fault scenarios] by implementing version-bound two-manager approval, PostgreSQL transaction locks, idempotent execution and a reconciled double-entry ledger in a paper-fund platform.
- Recovered [specific committed-state/notification behavior] under [documented crash/retry scenarios] by combining transactional outbox delivery, consumer deduplication and client snapshot resynchronization.
- Served [actual concurrency/operation mix] at [measured p95 latency and error rate] on [stated hardware] by [actual bottleneck fix]; retained [verified invariant result] under load.
- Promoted/rejected [candidate model] against [named baseline] using [chronological folds/holdout size and objective], then deployed [actual artifact/fallback] with point-in-time features, versioned batch inference and [measured monitoring evidence].

Do not copy the specification's targets into a resume. A test count should accompany its coverage meaning. A backtest must describe its costs/period/universe and should not suggest real-money returns. “SEC compliant” and “production scale” need evidence and appropriate context, and should normally be omitted here.

## Five-minute demo

1. Show paper mode, the two managers and equal capital accounts.
2. Propose a valid order, attempt self-approval, then have the other manager approve.
3. Show queued state and advance the fixture clock to the next open.
4. Replay the request; show one fill, settlement/ledger and reconciled NAV.
5. Trigger a concentration block or gap rejection and explain the risk rule.
6. Open the season report; show shared gains/losses and benchmark excess return.
7. For ML audiences, show a versioned prediction, baseline comparison and a failed-model/fallback case.

Keep the visuals readable enough that an interviewer can follow the system. Most preparation should go to explaining the hard decisions and their failure cases, not polishing a landing page.

## Interview questions to prepare

What happens when two buys compete for the same cash? Why does a retry not create another fill? How does an approval become stale? When is sale cash spendable? What if opening prices gap past a limit? How does a split affect quantity and basis? What data could leak into an HMM backtest? How can Redis be lost safely? Why reject a more complex model? What can your tests and short-season metrics not prove?

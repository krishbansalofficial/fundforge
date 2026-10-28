# ML showcase plan for a junior developer

Written 27 October 2026, revised the same day for the owner's framing: **a junior developer builds this, owns it, and must defend every line of it in interviews.** This is a proposal. It extends the 16 October revision in [ML_PLAN](ML_PLAN.md) and changes nothing until the owner accepts it in [DECISIONS](DECISIONS.md). Every metric below is a target to measure, not a result.

## The one rule

> Anything on the resume, you can explain for 15 minutes with no notes: what it does, one design choice and its alternative, how the result could be wrong.

Everything else in this plan follows from that rule.

## What the research says, for a junior

1. **Interviews are project deep dives.** Reported new-grad loops open with a 15-minute walkthrough of one resume project, chosen by the interviewer, followed by questions on data, model choices, evaluation design and what you would change ([PDT Partners report](https://prachub.com/interview-experiences/pdt-partners-machine-learning-engineer-interview-experience-project-deep-dive-then-a-find-divisors-follow-up), [project deep-dive prompt](https://prachub.com/interview-questions/end-to-end-ml-project-deep-dive-decisions-evaluation-design-and-career-goals), [Glassdoor junior MLE](https://static.glassdoor.fr/Interview/junior-machine-learning-engineer-interview-questions-SRCH_KO0,32_IP775.htm)).
2. **AI-built projects are checked for understanding.** 2026 guidance: say what the model drafted, and show where you accepted, rejected, edited or constrained its output. Unreviewed AI READMEs read as generic ([Provn](https://provn.co/blog/2026/06/campus-hiring-ai-native-builders), [TechInterview](https://www.techinterview.org/post/3233475399/ai-portfolio-built-with-ai-2026-interviews/), [SimeonOnSecurity](https://simeononsecurity.com/software-development-career-playbook/getting-started-in-software-development/building-a-developer-portfolio/)). **This is the biggest risk for this repo:** it is large and was mostly built with Claude.
3. **Depth over tool count.** Two to four deep, explained projects beat many shallow ones; too many entries hide the strong work ([Interview Kickstart](https://interviewkickstart.com/blogs/articles/machine-learning-engineer-portfolio), [Lyrid](https://www.lyrid.io/post/5-critical-software-engineer-portfolio-mistakes-that-junior-developers-are-making)). A list like Kafka + Debezium + Spark + K8s on a junior resume invites "explain the Debezium connector config", and a weak answer costs more than the line earns.
4. **A live link helps.** Several guides want a deployed demo or a clickable result, not only a repo ([Interview Kickstart](https://interviewkickstart.com/blogs/articles/machine-learning-engineer-portfolio)). For this project, a static results page or recorded demo is enough. Any public deployment needs the owner's explicit decision (CLAUDE.md).
5. **The standard RL learning path** is fundamentals (Sutton & Barto or Silver's lectures), then Spinning Up's PPO, then CleanRL's single-file PPO, then your own implementation ([Spinning Up](https://my-spinning-up.readthedocs.io/en/latest/), [CleanRL tutorial](https://pettingzoo.farama.org/tutorials/cleanrl/)). None of the sources give a timeline; the estimates below are judgement.

Caveat: most hiring sources are career blogs and candidate reports, not hiring data.

## Ownership audit: what to lead with, learn, or drop

| Component | On the resume? | What you must be able to explain |
|---|---|---|
| Gymnasium env, action masks, leak canary | **Lead** | Why masks come from the observation only; what the canary test plants and why it proves no leak |
| Forecaster vs exact Bayes filter | **Lead** | What a Bayes filter is; Brier and ECE; why family-level splits matter; why you stopped at a 0.0004 gap |
| MaskablePPO result | Lead *after* Stage 1 fixes it | Today: 1 seed, 14 worlds, random also wins. Do not quote it yet |
| Eval statistics (`evals.py`) | Lead, once you wrote `prob_improvement` | Bootstrap, IQM, why pairing by world tightens intervals |
| Postgres outbox → Debezium → Kafka | **One supporting line at most** | The transactional-outbox pattern in 2 minutes. If you can't, leave it off |
| Engine, journal, fund accounting | Context only | "Deterministic simulator with exact replay"; you don't need the fee maths for an ML interview |
| Spark, Ray, K8s, Dagster, MAPPO, PAIRED | **Drop** | Not built; don't list them |

## The plan (about 9 weeks at about 15 hours a week)

Each stage says what **you write by hand** and where Claude may help (scaffolding, tests, review, explanations). Estimates are for a junior learning as they go, about 2–3× what a senior would need.

### Stage 1: honest evaluation (weeks 1–2)

| You write | Claude may help with |
|---|---|
| `evals.prob_improvement`; the multi-seed loop and result table in `train_ppo.py`; hyperparameter choice on the validation split | Wiring, test scaffolding, review |

- **Deliverable:** `ppo_pm.json` with 5 training seeds and at least 100 test families, reported through `evals` (IQM, bootstrap CI, P(X>Y)), plus a difficulty sweep that shows how often random play stops winning.
- **Learn:** the rliable paper's figures ([blog](https://research.google/blog/rliable-towards-reliable-evaluation-reporting-in-reinforcement-learning/)) and what a percentile bootstrap does.
- **Interview question it prepares:** "How do you know PPO is actually better than random?"

### Stage 2: PPO from scratch (weeks 3–5), the centrepiece

| You write | Claude may help with |
|---|---|
| A single-file PPO with action masking (about 300 lines, CleanRL style): rollout buffer, GAE, clipped loss, masked logits | Explaining each equation, reviewing your code, a test harness |

- **Deliverable:** your PPO trained on `FundForgeEnv`, then compared with the SB3 MaskablePPO on the same worlds and seeds using `evals.compare`. The acceptance target is "not worse than SB3 within the CI". If it is worse, find out why and write it up; that write-up is worth as much as a win. Then a masking ablation: your PPO with masks vs. invalid actions penalised.
- **Learn:** Spinning Up's PPO page, then CleanRL `ppo.py` line by line, then the "37 implementation details of PPO" blog post.
- **Why this is the centrepiece:** "I implemented PPO, verified it against a library and found X" is a story a junior can own completely, and it answers "do you understand the algorithm or just call `.learn()`?"

### Stage 3: one differentiator, value of information (weeks 6–7)

| You write | Claude may help with |
|---|---|
| The observation wrapper that appends a belief; the experiment script and the analysis | Checking that the belief input uses public prints only (leak review) |

- **Deliverable:** the same PPO with three inputs: no belief, the learned forecaster's P(stressed), and the exact Bayes P(stressed). All three use public, as-of data only, so nothing leaks. Report how much return a better belief buys.
- **Why this one:** it joins your two strongest pieces (forecaster and RL) into one question that most projects can't ask, because they have no exact posterior. It needs no new infrastructure.

### Stage 4: the showcase (weeks 8–9)

| You write | Claude may help with |
|---|---|
| `ml/README.md` **in your own words**; a 2-page write-up; an "How I used AI" section; a 3-minute demo video script | Checking that every number links to a result file; proofreading |

- **Results table:** every number links to a JSON in `ml/results/` with its commit, seeds and reproduce command.
- **"How I used AI":** what Claude generated, what you rewrote (your PPO, `evals`), and one AI suggestion you rejected and why. The research says this section now helps rather than hurts.
- **Resume bullet template** (fill in measured numbers only):
  - *Built a Gymnasium environment for a deterministic hedge-fund simulator with action masking and leak-canary tests; implemented PPO from scratch and matched Stable-Baselines3 within [CI] over [N] seeds × [M] held-out worlds.*
  - *Forecaster within [gap] Brier of the exact Bayes-optimal posterior on [N] held-out world families; showed a better belief adds [X] reward to the RL policy.*

## Later, only if Stages 1–4 are done

Ranked for junior-friendliness: small libraries, short code, easy to explain.

1. **Anomaly detection on the books.** scikit-learn `IsolationForest` on journal-line features, scored on the labelled B5 fault corpus. Report recall at 1% FPR per fault class next to the rule-based controls. About 1 week.
2. **VIPER-style distillation.** A scikit-learn decision tree imitating your PPO (DAgger loop). Report action agreement, return kept and tree depth; print the rules ([Bastani et al. 2018](https://arxiv.org/abs/1805.08328)). About 1 week.
3. **Local LLM in the bot seat**, via Ollama, zero spend. Scored with the same `evals`. About 2 weeks; mostly prompt and tool-schema work, and harder to evaluate than it looks.

**Not for now:** two-seat MAPPO, PAIRED world search, a population-based exploit hunter, Spark/Ray/K8s. Each is a research or platform project of its own.

## Interview drill (answer each aloud, without notes, before listing the project)

1. Walk me through the project in 2 minutes.
2. Why PPO and not DQN? What does the clip do?
3. How do you prevent the agent from seeing the future?
4. Why split by seed family instead of by row?
5. Your forecaster is 0.0004 Brier from optimal; how do you know the optimum?
6. How many seeds, and why is one not enough?
7. What did the masking ablation show?
8. What would break if the generator changed?
9. What did you write, and what did AI write?
10. What would you do with two more months?

## Working with Claude on this

- Claude explains, reviews, scaffolds and writes tests. **You write the core logic listed in each stage.**
- After each stage, write the half-page explain-back from ML_PLAN without Claude, and have Claude quiz you on it.
- Never quote a number that isn't in a result file.

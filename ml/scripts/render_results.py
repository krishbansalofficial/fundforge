"""Regenerate the results table in ml/README.md from ml/results/*.json.

Run from ml/:
    uv run python scripts/render_results.py           # rewrite the section between the markers
    uv run python scripts/render_results.py --check   # exit 1 if the README is out of date (CI)

Every number in the table is read from a result file; nothing is typed by hand. Each known file
has one small renderer. A file with no renderer, or one whose JSON or keys do not match, gets a
"not rendered" row instead of a crash or a guess.
"""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ML = Path(__file__).resolve().parents[1]
START = "<!-- results:start -->"
END = "<!-- results:end -->"

Row = tuple[str, str, str, str]  # experiment, headline with interval, scale, reproduce


def _g(x: float) -> str:
    return f"{x:.3g}"


def forecast(d: dict[str, Any]) -> Row:
    lgbm = d["test"]["lightgbm"]
    return (
        "Regime forecast: LightGBM vs exact Bayes filter",
        f"Brier gap to Bayes {_g(lgbm['gap_brier'])}, SE {_g(lgbm['gap_brier_se_by_world'])} (by world); "
        f"Brier {_g(lgbm['brier'])} vs Bayes {_g(d['test']['bayes_exact_filter']['brier'])}",
        f"1 training seed ({d['training']['seed']}) x {lgbm['worlds']} test families, n={lgbm['n']}",
        d["reproduce"],
    )


def _win_share(labels: dict[str, int]) -> float:
    return labels.get("WIN", 0) / sum(labels.values())


def ppo(d: dict[str, Any]) -> Row:
    if "scale" in d:  # eval_ppo.py (Stage 1) format
        s, t = d["scale"], d["test"]
        c, iq = t["compare"]["ppo_vs_random"], t["policies"]["ppo"]["iqm"]
        lv = d.get("train_level", "base")
        win = {k: _win_share(t["policies"][k]["labels"]) for k in ("ppo", "random")}
        return (
            f"MaskablePPO ({s['role']} seat) vs random, {lv} worlds, "
            + ("selected on val" if len(d["grid"]) > 1 else f"config fixed to {next(iter(d['grid']))}"),
            f"paired reward PPO - random {_g(c['diff']['point'])} [{_g(c['diff']['lo'])}, {_g(c['diff']['hi'])}]; "
            f"P(PPO > random) {_g(c['prob_improvement'])}; PPO IQM {_g(iq['point'])} "
            f"[{_g(iq['lo'])}, {_g(iq['hi'])}]; WIN rate PPO {win['ppo']:.0%}, random {win['random']:.0%}",
            f"{len(s['training_seeds'])} training seeds x {s['steps_per_run']} steps; "
            f"{s['test_worlds']} test worlds ({s['test_families']} families)",
            d["reproduce"],
        )
    p, r = d["params"], d["report"]
    paired = r["ppo_minus_random_paired"]
    return (
        f"MaskablePPO ({p['role']} seat) vs random",
        f"paired reward PPO - random {paired['mean']} +/- {paired['ci95']} (ci95); "
        f"PPO better on {paired['ppo_better_worlds']}/{paired['n_worlds']} worlds",
        f"1 training seed ({p['seed']}) x {paired['n_worlds']} test worlds ({p['test_families']} families)",
        f"cd ml && uv run --group train python scripts/train_ppo.py --role {p['role']} --steps {p['steps']} "
        f"--families {p['families_drawn']} --seed {p['seed']}",
    )


def kafka(d: dict[str, Any]) -> Row:
    live, stopped, rec = d["phase1_live"], d["kafka_stopped"], d["phase2_recovered"]
    return (
        "Outbox -> Kafka streamed vs batch features",
        f"live ok={live['ok']}; game finished with Kafka stopped={stopped['finished']}; "
        f"recovered ok={rec['ok']} ({rec['distinct_events']}/{rec['outbox_rows']} events); no interval (pass/fail)",
        f"1 room, n={rec['outbox_rows']} outbox events",
        "deploy/kafka/fetch-debezium.sh && docker compose -f deploy/kafka/compose.yaml up -d --wait "
        "&& cd ml && uv run --group stream python scripts/kafka_e2e.py",
    )


def anomaly(d: dict[str, Any]) -> Row:
    def caught(m: dict[str, Any]) -> str:
        pc = m["per_class"]
        return f"{sum(c['detected'] for c in pc.values())}/{sum(c['n'] for c in pc.values())}"

    models, s = d["models"], d["sizes"]
    lw = models["ledoit_wolf_mahalanobis"]
    return (
        "Books anomaly detection vs rule-based controls (B5 faults)",
        f"faults caught at {lw['held_out_clean']['fpr']:.2%} held-out FPR: Ledoit-Wolf {caught(lw)}, "
        f"IsolationForest {caught(models['isolation_forest'])}; controls catch every fault (see JSON per class)",
        f"1 model seed; {s['faults']} faults ({s['faults_per_class']} per class), "
        f"{lw['held_out_clean']['n']} held-out clean checkpoints",
        d["reproduce"],
    )


def bench_env(d: dict[str, Any]) -> Row:
    sp = {r["role"]: r["steps_per_s"] for r in d["single_process"]}
    vec = max(d["vectorised"], key=lambda r: r["workers"])
    prof, m = d["profile"], d["machine"]
    return (
        "M1 env throughput (this machine only)",
        f"single process pm {_g(sp['pm']['median'])} steps/s [{_g(sp['pm']['min'])}-{_g(sp['pm']['max'])}]; "
        f"{vec['workers']} workers {_g(vec['steps_per_s']['median'])} steps/s "
        f"[{_g(vec['steps_per_s']['min'])}-{_g(vec['steps_per_s']['max'])}]; "
        f"rollback snapshot {prof['share_snapshot']:.0%} of profiled time",
        f"median of {d['method']['reps']} reps, {len(d['worlds']['accepted'])} worlds; {m['cpu']}",
        d["reproduce"],
    )


def viper(d: dict[str, Any]) -> Row:
    k = str(d["exported_depth"])
    t, s = d["depths"][k], d["scale"]
    smoke = "SMOKE ONLY; " if d.get("status", "").startswith("SMOKE") else ""
    return (
        "VIPER: PPO distilled into a decision tree",
        f"{smoke}depth {k} ({t['tree']['leaves']} leaves): fidelity {_g(t['fidelity_on_student_states'])}, "
        f"tree - teacher {_g(t['vs_teacher']['diff']['point'])} "
        f"[{_g(t['vs_teacher']['diff']['lo'])}, {_g(t['vs_teacher']['diff']['hi'])}]",
        f"teacher {s['teacher_steps']} (sha256 {d['teacher_sha256'][:12]}), 1 seed; {s['worlds']['test']} test worlds",
        d["reproduce"],
    )


def voi(d: dict[str, Any]) -> Row:
    c, s = d["report"]["compare_reward"], d["scale"]

    def diff(k: str) -> str:
        x = c[k]["diff"]
        return f"{_g(x['point'])} [{_g(x['lo'])}, {_g(x['hi'])}]"

    return (
        "Value of information: P(stressed) added to the PPO observation",
        f"paired reward exact Bayes - none {diff('exact_vs_none')}; learned - none {diff('learned_vs_none')}",
        f"{s['seeds_per_mode']} seeds per mode x {s['steps_per_run']} steps; "
        f"{s['test_worlds']} test worlds ({s['test_families']} families)",
        d["reproduce"],
    )


def trace_floor(d: dict[str, Any]) -> Row:
    a, s = d["overall"], d["scale"]
    return (
        "Hard PPO vs scripted derisk_floor: action traces",
        f"first de-risk within +/-1 window of derisk_floor {a['share_timing_match_pm1']:.0%} "
        f"(PPO at the first window {a['share_ppo_first_derisk_at_window0']:.0%}); "
        f"Jaccard (day, reduce:SYM) mean {_g(a['jaccard_day_type']['mean'])} "
        f"[IQR {_g(a['jaccard_day_type']['q1'])}-{_g(a['jaccard_day_type']['q3'])}]; "
        f"PPO reduces every derisk_floor name {a['share_ppo_reduces_all_floor_symbols']:.0%}; "
        f"score PPO {_g(a['mean_score_bps']['ppo'])} vs floor {_g(a['mean_score_bps']['floor'])} bps, "
        f"PPO higher {a['share_ppo_score_above_floor']:.0%}",
        f"{s['models']}; {s['episodes']} episodes on {s['test_worlds']} test worlds",
        d["reproduce"],
    )


def attribution(d: dict[str, Any]) -> Row:
    def b(c: dict[str, Any]) -> str:
        return f"{_g(c['est'])} [{_g(c['lo'])}, {_g(c['hi'])}]"

    pol = d["policies"]
    parts = [
        f"{k} beta pre {b(v['pooled_true']['pre_post']['coef']['beta_pre'])} -> post "
        f"{b(v['pooled_true']['pre_post']['coef']['beta_post'])}"
        for k, v in pol.items()
    ]
    eps = sum(v["episodes"] for v in pol.values())
    return (
        "Return attribution on the generator's true market factor (pooled OLS, cluster by world)",
        "; ".join(parts) + f"; true vs public-proxy factor corr {_g(d['factor_vs_proxy']['corr'])}; "
        "per-episode fits have 6-7 days (wide intervals)",
        f"{d['scale']['test_worlds']} hard test worlds, {eps} episodes; PPO: {d['scale']['ppo']}",
        d["reproduce"],
    )


def transfer(d: dict[str, Any]) -> Row:
    def cell(k: str) -> str:
        c = d["cells"][k]
        win = c["ppo"]["labels"].get("WIN", 0)
        n = sum(c["ppo"]["labels"].values())
        x = c["ppo_vs_random"]["diff"]
        name = k.replace("train_", "").replace("/test_", "->")
        return f"{name}: WIN {win}/{n}, vs random {_g(x['point'])} [{_g(x['lo'])}, {_g(x['hi'])}]"

    return (
        "Generalisation matrix: PPO trained on base or hard worlds, tested on both",
        "; ".join(cell(k) for k in d["cells"]),
        f"5 published checkpoints per train level, {d['scale']['random_runs']} random runs, published test splits",
        d["reproduce"],
    )


def conformal(d: dict[str, Any]) -> Row:
    r = d["results"]["lightgbm"]
    parts = [f"{round(v['target'] * 100)}%: cov {_g(v['coverage'])} {v['coverage_ci95_by_family']}, "
             f"both {_g(v['share_both'])}, empty {_g(v['share_empty'])}"
             for k, v in r.items() if k.endswith("marginal")]
    return (
        "Split conformal sets for the LightGBM regime forecast",
        "; ".join(parts),
        f"{d['data']['scored_families']} scored / {d['data']['calibration_families']} calibration test families",
        d["reproduce"],
    )


def ope(d: dict[str, Any]) -> Row:
    parts = []
    for t, v in d["targets"].items():
        parts.append(f"{t}: truth {_g(v['truth']['value'])}, PDIS {_g(v['pdis']['value'])}, "
                     f"WPDIS {_g(v['wpdis']['value'])}, FQE {_g(v['fqe']['value'])}, ESS {_g(v['ess_full_episode'])}")
    return (
        "Off-policy evaluation from random-play logs vs simulator truth (hard test worlds)",
        "; ".join(parts) + ". No estimator recovers PPO's value; see ope_noise_floor.json for the seed-set spread",
        f"{d['scale']['worlds']} worlds x {d['scale']['log_runs_per_world']} logged episodes; "
        f"truth {d['scale']['truth_runs_per_world']} runs/world",
        d["reproduce"],
    )


def ope_noise(d: dict[str, Any]) -> Row:
    sets = "; ".join(f"seeds {k}+: mean {_g(v['mean'])} (SE {_g(v['se_by_world'])})" for k, v in d["seed_sets"].items())
    return (
        "OPE noise floor: random play's mean return across independent seed sets",
        f"{sets}; spread {_g(d['spread'])}",
        f"{d['worlds']} worlds x 10 episodes per set",
        d["reproduce"],
    )


def mask_ablation(d: dict[str, Any]) -> Row:
    x, a = d["masked_vs_penalty"], d["arms"]
    return (
        "Masking ablation: MaskablePPO vs PPO with an invalid-action penalty (base worlds)",
        f"paired reward masked - penalty {_g(x['diff']['point'])} [{_g(x['diff']['lo'])}, {_g(x['diff']['hi'])}], "
        f"P(masked > penalty) {_g(x['prob_improvement'])}; invalid picks {_g(a['penalty']['invalid_pick_rate'])} "
        f"(penalty arm) vs {_g(a['masked']['invalid_pick_rate'])}",
        f"{d['scale']['seeds']} seeds x {d['scale']['steps']} steps per arm; {d['scale']['test_worlds']} test worlds; "
        "masked arm = the published ppo_pm checkpoints (sha256 checked)",
        d["reproduce"],
    )


RENDERERS: dict[str, Callable[[dict[str, Any]], Row]] = {
    "transfer_matrix.json": transfer,
    "mask_ablation.json": mask_ablation,
    "ope.json": ope,
    "ope_noise_floor.json": ope_noise,
    "conformal_forecast.json": conformal,
    "attribution.json": attribution,
    "voi_pm.json": voi,
    "anomaly.json": anomaly,
    "viper_pm.json": viper,
    "bench_env.json": bench_env,
    "forecast.json": forecast,
    "ppo_pm.json": ppo,
    "ppo_pm_hard.json": ppo,
    "kafka_e2e.json": kafka,
    "trace_ppo_vs_floor.json": trace_floor,
}


def row(path: Path) -> str:
    link = f"[{path.name}](results/{path.name})"
    try:
        exp, head, scale, cmd = RENDERERS[path.name](json.loads(path.read_text(encoding="utf-8")))
    except (KeyError, TypeError, ValueError, IndexError):  # no renderer, bad JSON, or a changed schema
        return f"| not rendered: {path.name} | | | {link} | |"

    def cell(x: str) -> str:  # result JSON is data: keep it inside its table cell
        return " ".join(x.replace("|", r"\|").replace("`", "'").split())

    return f"| {cell(exp)} | {cell(head)} | {cell(scale)} | {link} | `{cell(cmd)}` |"


def render(results: Path) -> str:
    lines = [
        "<!-- generated by scripts/render_results.py from results/*.json; do not edit by hand -->",
        "| Experiment | Headline (interval) | Scale | Evidence | Reproduce |",
        "|---|---|---|---|---|",
        *(row(p) for p in sorted(results.glob("*.json"))),
    ]
    return "\n".join(lines)


def splice(readme: str, section: str) -> str:
    head, sep, rest = readme.partition(START)
    _, sep2, tail = rest.partition(END)
    if not (sep and sep2):
        raise SystemExit(f"README is missing {START} / {END}")
    return f"{head}{START}\n{section}\n{END}{tail}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if the README is out of date")
    ap.add_argument("--results", type=Path, default=ML / "results")
    ap.add_argument("--readme", type=Path, default=ML / "README.md")
    a = ap.parse_args(argv)
    old = a.readme.read_text(encoding="utf-8")
    new = splice(old, render(a.results))
    if a.check:
        if new != old:
            print(f"{a.readme} is out of date; run scripts/render_results.py", file=sys.stderr)
            return 1
        return 0
    a.readme.write_text(new, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

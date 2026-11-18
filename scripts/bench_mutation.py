"""Benchmark B5 (second half): mutation score for the accounting and control modules.

Stdlib only. One AST mutant at a time is written into a temporary copy of backend/src (never the working
tree); the module's test files run against the copy with `pytest -x -q` and a timeout.

    cd backend && uv run python ../scripts/bench_mutation.py --out ../bench/results
    ... --sample 60 --seed 1          # at most 60 mutants per module, seeded
    ... --modules shadow broker       # subset
    ... --selftest                    # check the mutant generator only

Operators: cmp (< <=, > >=, == !=, in/not in, is/is not), arith (+ -, including += -=), const (int n -> n+1,
True <-> False), bool (and <-> or, drop `not`, negate if/while/ternary/assert tests), raise (raise -> pass).
Not mutated: Decimal string literals, annotations, docstrings. Equivalent mutants are not filtered, so the
score is a lower bound on the kill rate of meaningful mutants.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import platform
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT / "scripts"))

from bench_engine import commit, machine  # noqa: E402

# module -> test files, cheapest first so -x kills early
TESTS = {
    "shadow": ["test_shadow", "test_fault_corpus", "test_certificate", "test_golden", "test_settlement_recon"],
    "administrator": ["test_redemption_half_cent", "test_fault_corpus", "test_administrator", "test_prospect"],
    "broker": ["test_broker", "test_shadow", "test_fault_corpus", "test_certificate"],
    "settlement_recon": ["test_shadow", "test_fault_corpus", "test_settlement_recon"],
    "journal": ["test_journal", "test_invariants", "test_engine", "test_golden", "test_fault_corpus"],
    "series": ["test_series", "test_redemption_half_cent", "test_golden", "test_fault_corpus"],
}

CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
       ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}
ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add}


def _sites(tree: ast.AST) -> list[tuple[int, int, str, int]]:
    """Every mutation site as (line, col, operator, index into ast.walk order); k distinguishes chained ops."""
    skip: set[int] = set()  # annotations and docstrings
    for n in ast.walk(tree):
        for f in ("annotation", "returns"):
            if getattr(n, f, None) is not None:
                skip.update(id(x) for x in ast.walk(getattr(n, f)))
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            skip.add(id(n.body[0].value))
    out = []
    for i, n in enumerate(ast.walk(tree)):
        if id(n) in skip:
            continue
        ops: list[str] = []
        if isinstance(n, ast.Compare):
            ops += [f"cmp:{k}" for k, o in enumerate(n.ops) if type(o) in CMP]
        elif isinstance(n, (ast.BinOp, ast.AugAssign)) and type(n.op) in ARITH:
            ops.append("arith")
        elif isinstance(n, ast.Constant) and isinstance(n.value, (bool, int)):
            ops.append("const")
        elif isinstance(n, ast.BoolOp):
            ops.append("bool:andor")
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            ops.append("bool:dropnot")
        elif isinstance(n, (ast.If, ast.While, ast.IfExp, ast.Assert)):
            ops.append("bool:negate")
        elif isinstance(n, ast.Raise):
            ops.append("raise")
        out += [(n.lineno, n.col_offset, op, i) for op in ops]
    return sorted(out)


def _apply(tree: ast.AST, op: str, index: int) -> str:
    tree = copy.deepcopy(tree)
    parents = {id(c): (p, f) for p in ast.walk(tree) for f, v in ast.iter_fields(p)
               for c in (v if isinstance(v, list) else [v]) if isinstance(c, ast.AST)}
    n = list(ast.walk(tree))[index]

    def replace(new: ast.AST) -> None:
        p, f = parents[id(n)]
        v = getattr(p, f)
        if isinstance(v, list):
            v[v.index(n)] = new
        else:
            setattr(p, f, new)

    kind, _, k = op.partition(":")
    if kind == "cmp":
        n.ops[int(k)] = CMP[type(n.ops[int(k)])]()
    elif kind == "arith":
        n.op = ARITH[type(n.op)]()
    elif kind == "const":
        n.value = (not n.value) if isinstance(n.value, bool) else n.value + 1
    elif k == "andor":
        n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
    elif k == "dropnot":
        replace(n.operand)
    elif k == "negate":
        n.test = ast.UnaryOp(op=ast.Not(), operand=n.test)
    elif kind == "raise":
        replace(ast.Pass())
    return ast.unparse(ast.fix_missing_locations(tree))


def mutants(source: str) -> list[dict]:
    tree = ast.parse(source)
    same = ast.unparse(tree)
    out = []
    for line, col, op, index in _sites(tree):
        code = _apply(tree, op, index)
        if code != same:
            out.append({"line": line, "col": col, "operator": op, "code": code})
    return out


def _pytest(pkg_parent: Path, tests: list[str], timeout: float) -> tuple[str, float]:
    env = {"FUNDFORGE_FIXTURES": str(ROOT / "fixtures"), **os.environ, "PYTHONPATH": str(pkg_parent),
           "PYTHONDONTWRITEBYTECODE": "1"}
    cmd = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *[f"tests/{t}.py" for t in tests]]
    t0 = time.perf_counter()
    try:
        rc = subprocess.run(cmd, cwd=BACKEND, env=env, capture_output=True, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        return "timeout", time.perf_counter() - t0
    # 0 = all passed; 1 = a test failed; 2 = collection/import error (mutant broke the module). Both are kills.
    return ("survived" if rc == 0 else "killed" if rc in (1, 2) else f"error:{rc}"), time.perf_counter() - t0


def selftest() -> None:
    src = 'def f(a: int = 1) -> int:\n    "doc"\n    if a < 2 and not a:\n        raise ValueError\n    return a + 1\n'
    ms = mutants(src)
    assert [m["operator"] for m in ms] == ["const", "bool:negate", "bool:andor", "cmp:0", "const", "bool:dropnot",
                                           "raise", "arith", "const"], [m["operator"] for m in ms]
    assert "a <= 2" in ms[3]["code"] and "pass" in ms[6]["code"] and "a - 1" in ms[7]["code"]
    assert all(compile(m["code"], "m", "exec") for m in ms) and mutants(src) == ms  # valid and deterministic
    print("selftest ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modules", nargs="+", default=list(TESTS), choices=list(TESTS))
    ap.add_argument("--sample", type=int, help="at most N mutants per module (seeded); default all")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0

    src = BACKEND / "src"
    started = time.perf_counter()
    modules: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="ff-mut-") as tmp:
        trees: queue.Queue[Path] = queue.Queue()
        for w in range(args.workers):
            shutil.copytree(src, Path(tmp) / f"w{w}", ignore=shutil.ignore_patterns("__pycache__"))
            trees.put(Path(tmp) / f"w{w}")

        for mod in args.modules:
            rel = Path("fundforge") / f"{mod}.py"
            original = (src / rel).read_text(encoding="utf-8")
            allm = mutants(original)
            picked = allm
            if args.sample and args.sample < len(allm):
                picked = sorted(random.Random(f"B5-mutation:{mod}:{args.seed}").sample(allm, args.sample),
                                key=lambda m: (m["line"], m["col"], m["operator"]))
            # negative check: the unmutated copy must pass, else a "kill" proves nothing
            status, base_s = _pytest(Path(tmp) / "w0", TESTS[mod], 600)
            if status != "survived":
                print(f"{mod}: baseline tests {status}; aborting", file=sys.stderr)
                return 2
            timeout = base_s * 3 + 30

            def run(m: dict, rel: Path = rel, original: str = original, mod: str = mod,
                    timeout: float = timeout) -> str:
                tree = trees.get()
                try:
                    (tree / rel).write_text(m["code"], encoding="utf-8")
                    return _pytest(tree, TESTS[mod], timeout)[0]
                finally:
                    (tree / rel).write_text(original, encoding="utf-8")
                    trees.put(tree)

            t0 = time.perf_counter()
            with ThreadPoolExecutor(args.workers) as pool:
                statuses = list(pool.map(run, picked))
            count = {s: statuses.count(s) for s in ("killed", "survived", "timeout")}
            errors = [s for s in statuses if s.startswith("error")]
            modules[mod] = {
                "file": f"backend/src/{rel.as_posix()}",
                "tests": TESTS[mod],
                "mutants_generated": len(allm),
                "total": len(picked),
                "sampled": len(picked) < len(allm),
                **count,
                "errors": len(errors),
                "score": round(count["killed"] / len(picked), 4) if picked else None,
                "baseline_seconds": round(base_s, 1),
                "timeout_seconds": round(timeout, 1),
                "wall_seconds": round(time.perf_counter() - t0, 1),
                "survivors": [f"backend/src/{rel.as_posix()}:{m['line']}:{m['col']} {m['operator']}"
                              for m, s in zip(picked, statuses, strict=True) if s == "survived"],
                "timeouts": [f"backend/src/{rel.as_posix()}:{m['line']}:{m['col']} {m['operator']}"
                             for m, s in zip(picked, statuses, strict=True) if s == "timeout"],
            }
            r = modules[mod]
            print(f"{mod}: {r['killed']}/{r['total']} killed, {r['survived']} survived, {r['timeout']} timeout "
                  f"(of {r['mutants_generated']} generated) in {r['wall_seconds']}s", flush=True)

    doc = {
        "benchmark": "B5-mutation-score",
        "commit": commit(),
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "machine": machine(),
        "tool": "scripts/bench_mutation.py (stdlib ast; not mutmut)",
        "operators": {
            "cmp": "< <=, > >=, == !=, in/not in, is/is not (one operator per mutant)",
            "arith": "+ <-> - (binary and augmented)",
            "const": "int n -> n+1; True <-> False",
            "bool": "and <-> or; drop `not`; negate if/while/ternary/assert test",
            "raise": "raise -> pass",
        },
        "sample": {"per_module": args.sample, "seed": args.seed} if args.sample else None,
        "workers": args.workers,
        "score_definition": "killed / total; timeouts and survivors both count against the score",
        "limits": [
            "equivalent mutants are not filtered; survivors need reading before being called test gaps",
            "Decimal string literals, annotations and docstrings are not mutated",
            "each module runs only its listed test files, not the whole suite",
            "pytest -x: a kill records only that some test failed, not which",
        ],
        "wall_seconds": round(time.perf_counter() - started, 1),
        "modules": modules,
    }
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        name = f"{doc['measured_at'][:10]}-B5-mutation-{doc['commit'].replace('+', '_')}.json"
        (args.out / name).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

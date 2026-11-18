"""Attribution: OLS recovers known betas; the generator's true factors stay hidden until the episode ends."""

import numpy as np
import pytest
from fundforge.engine import Engine
from fundforge.generator import HARD_VERSION, Spec, generate
from fundforge.tape import compile_tape

from fundforge_ml import attribution as A
from fundforge_ml import worlds


def test_fit_recovers_known_betas() -> None:
    pytest.importorskip("statsmodels")
    rng = np.random.default_rng(7)
    f = rng.uniform(-0.015, 0.015, 600)
    post = np.arange(600) >= 300
    y = 0.0005 + 1.1 * f * ~post + 0.4 * f * post + rng.normal(0, 0.002, 600)
    out = A.fit(y.tolist(), np.column_stack([f * ~post, f * post]).tolist(), ["pre", "post"])
    for k, true in (("alpha", 0.0005), ("pre", 1.1), ("post", 0.4)):
        c = out["coef"][k]
        assert c["lo"] < true < c["hi"] and abs(c["est"] - true) < 0.05, (k, c)
    assert out["se"].endswith(f"maxlags={A.nw_lags(600)}") and out["r2"] > 0.8


def test_true_factors_hidden_until_finished() -> None:
    raw = generate("attr-0", HARD_VERSION, worlds.skeleton(), Spec())
    for variant in ("base", "rally"):
        e = Engine(compile_tape(raw, variant))
        e.advance()
        while not e.finished():
            with pytest.raises(RuntimeError, match="hidden until the episode is finished"):
                A.true_factors(e, "attr-0")
            e.advance()
        truth = A.true_factors(e, "attr-0")  # replays and checks every mark against generate's output
        assert [[d, t["regime"]] for d, t in truth.items()] == raw["generator"]["regimes"]
        crisis = raw["generator"]["scenario"]["crisis_day"]
        broken = [d for d, t in truth.items() if not t["continuous"]]
        assert broken == ([] if variant == "base" else [crisis + 1])

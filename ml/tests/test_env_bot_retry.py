"""Regression: a bot ticket the engine rejects must not stall the clock (mp seat, harsh generated world).

bot:v1 in the pm seat retried a rejected margin-cure ticket on every pass; each retry's chat note
cleared the agent's readiness, so ``FundForgeEnv.step`` raised "time did not advance".
"""

from fundforge.generator import SCENARIO_VERSION, Spec, generate
from fundforge.tape import compile_tape

from fundforge_ml import worlds
from fundforge_ml.env import FundForgeEnv

HARSH = Spec(crisis_points=10, margin_points=25, factor_bp=400, idio_bp=250, stress_multiplier=5)  # eval_ppo "harsh"


def test_rejected_bot_ticket_does_not_stall_the_clock() -> None:
    w = worlds.World(compile_tape(generate("ppo-5", SCENARIO_VERSION, worlds.skeleton(), HARSH), "base"),
                     "ppo-5", "base")
    env = FundForgeEnv("mp", policy_id="wait", world_fn=lambda o, r: w)
    env.reset(seed=0)
    term = trunc = False
    while not (term or trunc):
        _, _, term, trunc, _ = env.step(0)
    assert term
    assert env.s is not None
    refused = [m for m in env.s.chat if str(m.get("text", "")).startswith("I tried to ticket")]
    assert refused, "world no longer rejects a bot ticket; pick another seed for this regression"
    assert len(refused) == len({m["ref"] for m in refused})  # one note per ref, never a retry loop

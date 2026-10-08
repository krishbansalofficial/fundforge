"""Game balance: decisions under uncertainty must matter.

The tape has hidden variants (a day-16 sell-off or a rally). A player decides without knowing
which world they are in. Balance means: degenerate plays are illegal, every reasonable line
can win, and no policy is the best choice in every world (no strict dominance).
"""

from policy_grid import POLICIES, play

VARIANTS = ("base", "rally")
RESULTS = {name: {v: play(v, plan) for v in VARIANTS} for name, plan in POLICIES.items()}


def test_flattening_the_book_is_refused_by_the_mandate():
    for v in VARIANTS:
        assert RESULTS["flatten_d12"][v]["journal_digest"] == RESULTS["passive"][v]["journal_digest"]


def test_lines_that_handle_the_recall_win_in_every_world():
    for name in ("derisk_floor", "S1_balanced", "cover_recall_only"):
        assert all(RESULTS[name][v]["label"] == "WIN" for v in VARIANTS), name


def test_doing_nothing_never_wins():
    assert all(RESULTS["passive"][v]["label"] != "WIN" for v in VARIANTS)


def test_no_policy_is_best_in_every_world():
    best = {v: max(RESULTS, key=lambda n: float(RESULTS[n][v]["score"])) for v in VARIANTS}
    assert len(set(best.values())) > 1, f"dominant strategy: {best}"
    for name in RESULTS:
        beaten_somewhere = any(float(RESULTS[o][v]["score"]) > float(RESULTS[name][v]["score"])
                               for v in VARIANTS for o in RESULTS if o != name)
        assert beaten_somewhere, f"{name} dominates every policy in every world"

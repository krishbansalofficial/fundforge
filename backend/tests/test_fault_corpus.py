"""B5 smoke: a small seeded corpus; every authored class is caught independently, clean seasons are never flagged."""

from fault_corpus import CLASSES, corpus, evaluate, make


def test_small_corpus_detects_every_class_independently_with_no_false_positives():
    out = corpus(seeds=4)
    for cls, row in out["summary"]["per_class"].items():
        assert row["n"] == 4 and row["independent"] == 4, (cls, row)
    assert out["summary"]["clean"]["seasons"] == 8
    assert out["summary"]["clean"]["flagged_checkpoints"] == 0, [c for c in out["clean"] if c["flagged"]]


def test_corpus_is_seeded_and_deterministic():
    for cls in CLASSES:
        assert evaluate(make(cls, 7)) == evaluate(make(cls, 7))

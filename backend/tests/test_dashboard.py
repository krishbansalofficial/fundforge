"""The Grafana dashboard only queries series this API exports, with labels those series carry."""

import json
import re
from pathlib import Path

from prometheus_client import REGISTRY, generate_latest
from prometheus_client.parser import text_string_to_metric_families

import fundforge.observability  # noqa: F401  (registers the metrics)
from fundforge.observability import COMMAND_SECONDS, REJECTIONS

DASHBOARD = Path(__file__).parents[2] / "deploy" / "grafana" / "fundforge.json"


def test_every_panel_queries_an_exported_series_and_label():
    COMMAND_SECONDS.labels(type="ready").observe(0.01)  # make labelled series appear in the exposition
    REJECTIONS.labels(code="rejected").inc(0)
    exported: dict[str, set[str]] = {}
    for fam in text_string_to_metric_families(generate_latest(REGISTRY).decode()):
        for sample in fam.samples:
            exported.setdefault(sample.name, set()).update(sample.labels)
    panels = json.loads(DASHBOARD.read_text(encoding="utf-8"))["panels"]
    assert len(panels) == 4 and len({p["id"] for p in panels}) == 4
    for p in panels:
        for t in p["targets"]:
            names = set(re.findall(r"fundforge_[a-z_]+", t["expr"]))
            assert names and names <= set(exported), (p["title"], names - set(exported))
            by = set(re.findall(r"by \(([^)]*)\)", t["expr"])[0].replace(" ", "").split(","))
            labels = set().union(*(exported[n] for n in names))
            assert by <= labels, (p["title"], by - labels)

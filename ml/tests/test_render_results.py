"""scripts/render_results.py: rows come from the result files, bad files never crash, --check catches drift."""

import importlib.util
import shutil
from pathlib import Path

ML = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("render_results", ML / "scripts" / "render_results.py")
assert _spec and _spec.loader
rr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rr)


def _copy(tmp: Path) -> tuple[Path, Path]:
    results = tmp / "results"
    shutil.copytree(ML / "results", results)
    readme = tmp / "README.md"
    shutil.copy(ML / "README.md", readme)
    return results, readme


def test_committed_readme_is_current():
    assert rr.main(["--check"]) == 0


def test_renders_every_current_file():
    out = rr.render(ML / "results")
    for p in (ML / "results").glob("*.json"):
        assert f"(results/{p.name})" in out
    if (ML / "results" / "forecast.json").exists():
        assert "Brier gap to Bayes" in out


def test_malformed_and_unknown_files_get_not_rendered_rows(tmp_path):
    results, _ = _copy(tmp_path)
    (results / "forecast.json").write_text("{not json", encoding="utf-8")
    (results / "zz_new.json").write_text('{"anything": 1}', encoding="utf-8")
    out = rr.render(results)
    assert "| not rendered: forecast.json |" in out
    assert "| not rendered: zz_new.json |" in out


def test_check_detects_staleness_and_rewrite_fixes_it(tmp_path):
    results, readme = _copy(tmp_path)
    args = ["--results", str(results), "--readme", str(readme)]
    assert rr.main([*args, "--check"]) == 0
    (results / "zz_new.json").write_text("{}", encoding="utf-8")
    assert rr.main([*args, "--check"]) == 1
    assert rr.main(args) == 0
    assert rr.main([*args, "--check"]) == 0
    assert "not rendered: zz_new.json" in readme.read_text(encoding="utf-8")

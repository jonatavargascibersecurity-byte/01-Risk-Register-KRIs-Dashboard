"""Integration tests over the shipped data set."""

from dataclasses import replace
from pathlib import Path

from riskregister.registry import load_registry
from riskregister.report import build_report, data_fingerprint
from riskregister.dashboard import build_dashboard

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_data_loads_and_validates():
    registry = load_registry(DATA_DIR)
    assert len(registry.risks) >= 10
    assert registry.validate() == []


def test_validate_flags_bad_dates_scales_and_empty_status():
    registry = load_registry(DATA_DIR)
    bad_risk = replace(
        registry.risks[0],
        target_date="not-a-date",
        last_review="31/12/2026",
        residual_likelihood=9,
        status="",
    )
    bad_control = replace(registry.controls[0], last_tested="31/12/2026")
    mutated = replace(
        registry,
        risks=[bad_risk, *registry.risks[1:]],
        controls=[bad_control, *registry.controls[1:]],
    )

    issues = mutated.validate()
    assert any("target_date must be YYYY-MM-DD" in issue for issue in issues)
    assert any("last_review must be YYYY-MM-DD" in issue for issue in issues)
    assert any("residual_likelihood must be between" in issue for issue in issues)
    assert any("status is empty" in issue for issue in issues)
    assert any("last_tested must be YYYY-MM-DD" in issue for issue in issues)


def test_all_controls_and_kris_referenced():
    registry = load_registry(DATA_DIR)
    control_ids = {c.id for c in registry.controls}
    referenced = {cid for r in registry.risks for cid in r.control_ids}
    assert control_ids == referenced


def test_report_contains_key_sections():
    registry = load_registry(DATA_DIR)
    report = build_report(registry)
    assert "# Relatorio Executivo de Risco" in report
    assert "Sumario executivo" in report
    assert "Heat map de risco residual" in report
    assert "Painel de KRIs" in report
    assert data_fingerprint(DATA_DIR) in report


def test_dashboard_is_self_contained():
    registry = load_registry(DATA_DIR)
    html = build_dashboard(registry)
    assert html.startswith("<!DOCTYPE html>")
    assert "<svg" in html
    assert "http://" not in html and "https://" not in html
    assert "cdn" not in html.lower()


def test_breaches_are_above_appetite():
    registry = load_registry(DATA_DIR)
    for risk in registry.risks_above_appetite():
        appetite = registry.appetite_by_category[risk.appetite_ref]
        assert risk.residual_level != appetite.appetite_level

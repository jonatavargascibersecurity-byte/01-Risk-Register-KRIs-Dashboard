"""Integration tests over the shipped data set."""

from pathlib import Path

from riskregister.registry import load_registry
from riskregister.report import build_report, data_fingerprint
from riskregister.dashboard import build_dashboard

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_data_loads_and_validates():
    registry = load_registry(DATA_DIR)
    assert len(registry.risks) >= 10
    assert registry.validate() == []


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

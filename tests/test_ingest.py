"""Tests for the lab-findings ingestion adapter."""

from pathlib import Path

from riskregister.ingest import (
    build_ingest_markdown,
    load_lab_findings,
    validate_findings,
)
from riskregister.registry import load_registry

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "labs" / "findings.sample.csv"


def test_sample_findings_load_and_validate():
    registry = load_registry(ROOT / "data")
    findings = load_lab_findings(SAMPLE)
    assert len(findings) == 3
    assert validate_findings(findings, registry) == []


def test_unknown_risk_is_reported():
    registry = load_registry(ROOT / "data")
    findings = load_lab_findings(SAMPLE)
    broken = findings[0].__class__(**{**findings[0].__dict__, "risk_id": "R-999"})
    issues = validate_findings([broken], registry)
    assert any("unknown risk" in issue for issue in issues)


def test_markdown_links_platform_and_resolution():
    registry = load_registry(ROOT / "data")
    markdown = build_ingest_markdown(load_lab_findings(SAMPLE), registry)
    assert "https://tryhackme.com/room/cybergovernanceregulation" in markdown
    assert "R-007" in markdown
    assert "How it was solved" in markdown
    assert "residual" in markdown

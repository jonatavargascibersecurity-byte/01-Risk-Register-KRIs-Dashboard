"""Guard the explicit links to real platform content.

The repository must point to the actual room/course/module, not to a platform
home page. These tests fail if a link is removed or replaced by a generic URL.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PLATFORM_URLS = [
    "https://tryhackme.com/room/cybergovernanceregulation",
    "https://tryhackme.com/room/seriskmanagement",
    "https://app.letsdefend.io/training/lessons/incident-triage-assessment-and-escalation",
    "https://academy.hackthebox.com/course/preview/security-incident-reporting",
    "https://academy.hackthebox.com/course/preview/information-security-guidelines",
]


def test_readme_references_real_platform_content():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for url in PLATFORM_URLS:
        assert url in readme


def test_platforms_mapping_links_content_to_artefacts():
    doc = (ROOT / "PLATFORMS.md").read_text(encoding="utf-8")
    for url in PLATFORM_URLS:
        assert url in doc
    for artefact in ("risk-triage-thm.json", "kri-monitoring-letsdefend"):
        assert artefact in doc


def test_lab_findings_and_scenario_use_specific_urls():
    findings = (ROOT / "labs" / "findings.sample.csv").read_text(encoding="utf-8")
    scenario = (ROOT / "scenarios" / "kri-monitoring-letsdefend.json").read_text(
        encoding="utf-8"
    )
    for url in (
        "https://tryhackme.com/room/cybergovernanceregulation",
        "https://app.letsdefend.io/training/lessons/incident-triage-assessment-and-escalation",
        "https://academy.hackthebox.com/course/preview/security-incident-reporting",
    ):
        assert url in findings
    assert (
        "https://app.letsdefend.io/training/lessons/incident-triage-assessment-and-escalation"
        in scenario
    )

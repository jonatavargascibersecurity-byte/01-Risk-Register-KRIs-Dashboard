"""Tests for the playable challenge mode."""

from pathlib import Path

from riskregister.challenge import (
    batch_answers,
    build_result_markdown,
    find_scenario,
    is_correct,
    load_scenarios,
    solve,
)
from riskregister.registry import load_registry

ROOT = Path(__file__).resolve().parents[1]


def _load():
    return load_registry(ROOT / "data"), load_scenarios(ROOT / "scenarios")


def test_scenarios_load_with_platform_links():
    _, scenarios = _load()
    assert len(scenarios) == 2
    assert all(s.url.startswith("https://") for s in scenarios)
    assert {s.platform for s in scenarios} == {"TryHackMe", "LetsDefend"}


def test_answers_are_computed_from_the_register():
    registry, scenarios = _load()
    scenario = find_scenario(scenarios, "risk-triage-thm")
    answers = {q.id: solve(registry, q) for q in scenario.questions}
    assert answers == {
        "Q1": "R-002",
        "Q2": "R-002,R-013",
        "Q3": "Amarelo",
        "Q4": "40",
        "Q5": "Critico",
        "Q6": "R-002>R-001>R-011",
    }


def test_numeric_answers_accept_variants():
    assert is_correct("40", "40.0")
    assert is_correct("46.7", "46,7")
    assert is_correct("Amarelo", " amarelo ")
    assert not is_correct("40", "41")


def test_batch_answers_and_report():
    registry, scenarios = _load()
    scenario = find_scenario(scenarios, "risk-triage-thm")
    answers = batch_answers(
        scenario,
        "Q1=R-002;Q2=R-002,R-013;Q3=Amarelo;Q4=40;Q5=Critico;Q6=R-002>R-001>R-011",
    )
    assert set(answers) == {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6"}
    md = build_result_markdown(registry, scenario, answers)
    assert "Score:** 6/6" in md
    assert "tryhackme.com" in md

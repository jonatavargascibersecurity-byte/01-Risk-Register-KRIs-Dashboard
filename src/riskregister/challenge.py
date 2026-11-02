"""Playable risk-triage challenges built on top of the real register.

The point is not to hardcode a quiz. Each scenario references risks and KRIs by
ID and the expected answer is *computed* from the same scoring engine used by
the dashboard, so the exercise can never drift from the data.

Scenarios live in ``scenarios/*.json`` and each one names the platform room or
path it is based on. That keeps a direct link between study material and the
artefact produced here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import KRI, Risk
from .registry import Registry
from .scales import LEVEL_EN, level, reduction_pct, score

SUPPORTED_TYPES = {
    "top_residual",
    "above_appetite",
    "kri_status",
    "reduction",
    "level",
    "order",
}


@dataclass(frozen=True)
class Question:
    id: str
    type: str
    prompt: str
    risks: tuple[str, ...] = ()
    kri: str = ""
    category: str = ""
    likelihood: int = 0
    impact: int = 0


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    platform: str
    path: str
    url: str
    briefing: str
    questions: tuple[Question, ...]


def load_scenarios(directory: str | Path) -> list[Scenario]:
    base = Path(directory)
    if not base.exists():
        raise FileNotFoundError(f"scenarios directory not found: {base}")
    scenarios: list[Scenario] = []
    for path in sorted(base.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        questions = tuple(
            Question(
                id=item["id"],
                type=item["type"],
                prompt=item["prompt"],
                risks=tuple(item.get("risks", ())),
                kri=item.get("kri", ""),
                category=item.get("category", ""),
                likelihood=int(item.get("likelihood", 0)),
                impact=int(item.get("impact", 0)),
            )
            for item in raw["questions"]
        )
        scenarios.append(
            Scenario(
                id=raw["id"],
                title=raw["title"],
                platform=raw.get("platform", ""),
                path=raw.get("path", ""),
                url=raw.get("url", ""),
                briefing=raw.get("briefing", ""),
                questions=questions,
            )
        )
    return scenarios


def find_scenario(scenarios: list[Scenario], scenario_id: str) -> Scenario:
    for scenario in scenarios:
        if scenario.id == scenario_id:
            return scenario
    known = ", ".join(s.id for s in scenarios) or "(none)"
    raise ValueError(f"unknown scenario {scenario_id!r}; available: {known}")


def _risk(registry: Registry, risk_id: str) -> Risk:
    for risk in registry.risks:
        if risk.id == risk_id:
            return risk
    raise ValueError(f"scenario references unknown risk {risk_id!r}")


def _kri(registry: Registry, kri_id: str) -> KRI:
    for kri in registry.kris:
        if kri.id == kri_id:
            return kri
    raise ValueError(f"scenario references unknown KRI {kri_id!r}")


def _risks_above_appetite(registry: Registry, category: str) -> list[Risk]:
    return [
        risk
        for risk in registry.risks_above_appetite()
        if risk.appetite_ref == category
    ]


def solve(registry: Registry, question: Question) -> str:
    """Return the canonical expected answer for a question."""

    if question.type == "top_residual":
        risks = [_risk(registry, rid) for rid in question.risks]
        if not risks:
            raise ValueError(f"{question.id}: top_residual needs at least one risk")
        best = max(risks, key=lambda r: (r.residual_score, r.priority_score))
        return best.id

    if question.type == "above_appetite":
        breaches = _risks_above_appetite(registry, question.category)
        return ",".join(sorted(r.id for r in breaches)) or "NENHUM"

    if question.type == "kri_status":
        return _kri(registry, question.kri).status

    if question.type == "reduction":
        risk = _risk(registry, question.risks[0]) if question.risks else None
        if risk is None:
            raise ValueError(f"{question.id}: reduction needs one risk")
        value = reduction_pct(risk.inherent_score, risk.residual_score)
        return f"{value:g}"

    if question.type == "level":
        return level(score(question.likelihood, question.impact))

    if question.type == "order":
        risks = [_risk(registry, rid) for rid in question.risks]
        ordered = sorted(risks, key=lambda r: (-r.residual_score, -r.priority_score, r.id))
        return ">".join(r.id for r in ordered)

    raise ValueError(f"{question.id}: unsupported question type {question.type!r}")


def explain(registry: Registry, question: Question) -> str:
    """Human-readable reasoning for the expected answer."""

    if question.type == "top_residual":
        ranked = sorted(
            (_risk(registry, rid) for rid in question.risks),
            key=lambda r: (r.residual_score, r.priority_score),
            reverse=True,
        )
        return "; ".join(
            f"{r.id}={r.residual_score} ({LEVEL_EN[r.residual_level]})" for r in ranked
        )

    if question.type == "above_appetite":
        breaches = _risks_above_appetite(registry, question.category)
        if not breaches:
            return f"Nenhum risco de '{question.category}' acima do apetite aprovado."
        return "; ".join(
            f"{r.id}={r.residual_score} vs apetite {registry.appetite_by_category[r.appetite_ref].appetite_level}"
            for r in breaches
        )

    if question.type == "kri_status":
        kri = _kri(registry, question.kri)
        return (
            f"{kri.id} current={kri.current} {kri.unit} "
            f"({kri.direction}, green={kri.green}, amber={kri.amber}, red={kri.red})"
        )

    if question.type == "reduction":
        risk = _risk(registry, question.risks[0])
        return (
            f"{risk.id} inherent={risk.inherent_score} residual={risk.residual_score} "
            f"reduction={risk.reduction_pct}%"
        )

    if question.type == "level":
        value = score(question.likelihood, question.impact)
        return f"score={question.likelihood}x{question.impact}={value} -> {level(value)}"

    if question.type == "order":
        ordered = sorted(
            (_risk(registry, rid) for rid in question.risks),
            key=lambda r: (-r.residual_score, -r.priority_score, r.id),
        )
        return " > ".join(f"{r.id}({r.residual_score})" for r in ordered)

    return ""


def normalize(raw: str) -> str:
    return raw.strip().replace(" ", "").replace("->", ">").upper()


def is_correct(expected: str, answer: str) -> bool:
    got = normalize(answer)
    want = normalize(expected)
    if got == want:
        return True
    # Numeric answers: accept 62.5, 62,5 and ±0.1 tolerance.
    try:
        return abs(float(got.replace(",", ".")) - float(want.replace(",", "."))) <= 0.1
    except ValueError:
        return False


def run_scenario(registry: Registry, scenario: Scenario) -> tuple[int, list[str]]:
    """Interactively ask every question; return (score, report lines)."""

    correct = 0
    report: list[str] = [f"# Challenge: {scenario.title}", ""]
    if scenario.platform or scenario.path:
        report.append(
            f"**Fonte:** {scenario.platform} - {scenario.path} ({scenario.url})"
        )
        report.append("")
    if scenario.briefing:
        report.extend([scenario.briefing, ""])
    report.extend(["| # | Pergunta | Sua resposta | Correta | Resultado |", "|---|---|---|---|---|"])

    for index, question in enumerate(scenario.questions, start=1):
        expected = solve(registry, question)
        print("")
        print(f"[{index}/{len(scenario.questions)}] {question.prompt}")
        try:
            answer = input("> ")
        except EOFError:
            answer = ""
        ok = is_correct(expected, answer)
        correct += int(ok)
        print(f"  {'OK' if ok else 'X'} expected: {expected}")
        print(f"  why: {explain(registry, question)}")
        report.append(
            f"| {index} | {question.prompt} | {answer} | {expected} | "
            f"{'OK' if ok else 'X'} |"
        )

    report.extend(
        [
            "",
            f"**Score:** {correct}/{len(scenario.questions)}",
            "",
            f"**Fonte:** {scenario.url}",
            "",
        ]
    )
    return correct, report


def batch_answers(scenario: Scenario, raw: str) -> dict[str, str]:
    """Parse ``Q1=R-001;Q2=...`` (also accepts comma-separated pairs)."""

    answers: dict[str, str] = {}
    separators = ";" if ";" in raw else ","
    for chunk in raw.split(separators):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        answers[key.strip()] = value.strip()
    return answers


def build_result_markdown(
    registry: Registry, scenario: Scenario, answers: dict[str, str]
) -> str:
    correct = 0
    lines = [f"# Challenge: {scenario.title}", ""]
    if scenario.platform or scenario.path:
        lines.append(f"**Fonte:** {scenario.platform} - {scenario.path} ({scenario.url})")
        lines.append("")
    if scenario.briefing:
        lines.extend([scenario.briefing, ""])
    lines.extend(
        ["| # | Pergunta | Sua resposta | Correta | Resultado |", "|---|---|---|---|---|"]
    )
    for index, question in enumerate(scenario.questions, start=1):
        expected = solve(registry, question)
        answer = answers.get(question.id, "")
        ok = is_correct(expected, answer)
        correct += int(ok)
        lines.append(
            f"| {index} | {question.prompt} | {answer or '-'} | {expected} | "
            f"{'OK' if ok else 'X'} |"
        )
    lines.extend(
        [
            "",
            f"**Score:** {correct}/{len(scenario.questions)}",
            "",
            "## Raciocinio",
            "",
        ]
    )
    for question in scenario.questions:
        lines.append(f"- **{question.id}:** {explain(registry, question)}")
    lines.append("")
    return "\n".join(lines)

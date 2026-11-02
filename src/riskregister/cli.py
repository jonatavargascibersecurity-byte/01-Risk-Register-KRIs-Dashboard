"""Command line interface for the risk register.

Examples
--------
    python -m riskregister validate
    python -m riskregister summary
    python -m riskregister risks --top 10
    python -m riskregister kri
    python -m riskregister report --out build/risk-report.md
    python -m riskregister dashboard --out build/dashboard.html
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .challenge import (
    batch_answers,
    build_result_markdown,
    explain,
    find_scenario,
    is_correct,
    load_scenarios,
    run_scenario,
    solve,
)
from .dashboard import write_dashboard
from .ingest import build_ingest_markdown, load_lab_findings, validate_findings
from .models import KRI, Risk
from .registry import DataError, load_registry
from .report import build_report
from .scales import LEVEL_EN, level, score

DEFAULT_DATA_DIR = "data"
DEFAULT_OUT_DIR = "build"

STATUS_MARK = {"Verde": "[V]", "Amarelo": "[A]", "Vermelho": "[R]", "Sem dados": "[-]"}


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        print("(no records)")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    line = "  ".join(h.ljust(widths[index]) for index, h in enumerate(headers))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))


def _risk_rows(risks: list[Risk], top: int | None) -> list[list[str]]:
    ordered = sorted(risks, key=lambda r: r.priority_score, reverse=True)
    if top:
        ordered = ordered[:top]
    return [
        [
            risk.id,
            risk.category,
            risk.title[:46],
            str(risk.inherent_score),
            str(risk.residual_score),
            LEVEL_EN[risk.residual_level],
            risk.owner,
            risk.target_date,
        ]
        for risk in ordered
    ]


def _kri_rows(kris: list[KRI]) -> list[list[str]]:
    return [
        [
            kri.id,
            kri.name[:44],
            STATUS_MARK[kri.status],
            "-" if kri.current is None else f"{kri.current:g} {kri.unit}".strip(),
            "-" if kri.previous is None else f"{kri.previous:g}",
            kri.trend,
            kri.owner,
        ]
        for kri in sorted(kris, key=lambda k: (k.status != "Vermelho", k.id))
    ]


def cmd_validate(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    issues = registry.validate()
    if not issues:
        print("OK - data quality checks passed, no findings.")
        return 0
    print(f"{len(issues)} data quality finding(s):")
    for index, issue in enumerate(issues, start=1):
        print(f"  {index:>2}. {issue}")
    return 1


def cmd_summary(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    breaches = registry.risks_above_appetite()
    counts = {"Verde": 0, "Amarelo": 0, "Vermelho": 0, "Sem dados": 0}
    for kri in registry.kris:
        counts[kri.status] += 1
    avg = (
        round(sum(r.residual_score for r in registry.risks) / len(registry.risks), 1)
        if registry.risks
        else 0.0
    )
    print("=" * 68)
    print("RISK REGISTER SUMMARY")
    print("=" * 68)
    print(f"Risks registered        : {len(registry.risks)}")
    print(f"Above approved appetite : {len(breaches)}")
    print(f"Average residual score  : {avg}/25")
    print(f"Controls catalogued     : {len(registry.controls)}")
    print(f"KRIs monitored          : {len(registry.kris)}")
    print(
        "KRI status              : "
        f"{counts['Verde']} green / {counts['Amarelo']} amber / "
        f"{counts['Vermelho']} red / {counts['Sem dados']} no data"
    )
    if breaches:
        print("\nRisks above appetite:")
        for risk in breaches:
            print(
                f"  - {risk.id} [{risk.residual_score} {LEVEL_EN[risk.residual_level]}] "
                f"{risk.title} (owner: {risk.owner})"
            )
    return 0


def cmd_risks(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    _print_table(
        ["ID", "CATEGORY", "TITLE", "INH", "RES", "LEVEL", "OWNER", "TARGET"],
        _risk_rows(registry.risks, args.top),
    )
    return 0


def cmd_kri(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    _print_table(
        ["ID", "INDICATOR", "ST", "CURRENT", "PREV", "TREND", "OWNER"],
        _kri_rows(registry.kris),
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    out = Path(args.out) / "risk-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_report(registry), encoding="utf-8")
    print(f"report written: {out}")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    out = Path(args.out) / "dashboard.html"
    written = write_dashboard(registry, out)
    print(f"dashboard written: {written}")
    return 0


def cmd_challenge(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    try:
        scenarios = load_scenarios(args.scenarios)
    except FileNotFoundError as exc:
        print(f"scenario error: {exc}", file=sys.stderr)
        return 2

    if args.list or not args.scenario:
        print("Available challenges")
        print("-" * 68)
        for scenario in scenarios:
            print(f"  {scenario.id:<28} {scenario.title}")
            print(f"  {'':<28} {scenario.platform} | {scenario.path}")
            print(f"  {'':<28} {scenario.url} ({len(scenario.questions)} questions)")
        print("")
        print("Run one with: python -m riskregister challenge --scenario <id>")
        return 0

    scenario = find_scenario(scenarios, args.scenario)
    print("=" * 68)
    print(scenario.title)
    print("=" * 68)
    print(f"Source: {scenario.platform} - {scenario.path}")
    print(scenario.url)
    print("")
    if scenario.briefing:
        print(scenario.briefing)
        print("")

    if args.show_solution:
        for question in scenario.questions:
            print(f"{question.id}: {question.prompt}")
            print(f"  answer: {solve(registry, question)}")
            print(f"  why   : {explain(registry, question)}")
        return 0

    out = Path(args.out) / f"challenge-{scenario.id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.answers:
        answers = batch_answers(scenario, args.answers)
        markdown = build_result_markdown(registry, scenario, answers)
        correct = sum(
            1
            for question in scenario.questions
            if is_correct(solve(registry, question), answers.get(question.id, ""))
        )
        for question in scenario.questions:
            expected = solve(registry, question)
            given = answers.get(question.id, "")
            mark = "OK" if is_correct(expected, given) else "X"
            print(f"[{mark}] {question.id}: expected {expected} | got {given or '-'}")
    else:
        correct, lines = run_scenario(registry, scenario)
        markdown = "\n".join(lines)

    out.write_text(markdown, encoding="utf-8")
    print("")
    print(f"Score: {correct}/{len(scenario.questions)}")
    print(f"Result written: {out}")
    return 0 if correct == len(scenario.questions) else 1


def cmd_ingest(args: argparse.Namespace) -> int:
    registry = load_registry(args.data)
    try:
        findings = load_lab_findings(args.source)
    except FileNotFoundError as exc:
        print(f"ingest error: {exc}", file=sys.stderr)
        return 2

    issues = validate_findings(findings, registry)
    if issues:
        print(f"{len(issues)} ingest issue(s):")
        for index, issue in enumerate(issues, 1):
            print(f"  {index:>2}. {issue}")
        return 1

    out = Path(args.out) / "lab-findings.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_ingest_markdown(findings, registry), encoding="utf-8")

    print("ID      DATE        PLATFORM      RISK    SEVERITY")
    print("-" * 60)
    for finding in sorted(findings, key=lambda f: (f.date, f.finding_id)):
        print(
            f"{finding.finding_id:<8}{finding.date:<12}{finding.platform:<14}"
            f"{finding.risk_id:<8}{finding.severity}"
        )
    print("")
    print(f"findings ingested: {len(findings)}")
    print(f"linked risks    : {len({f.risk_id for f in findings})}")
    print(f"report written  : {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="riskregister",
        description="Risk register, KRI monitoring and executive reporting (GRC).",
    )
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA_DIR,
        help=f"directory with the CSV data files (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT_DIR,
        help=f"output directory for generated artefacts (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="ISO timestamp used for the report header (default: now, UTC)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="run data quality checks").set_defaults(
        func=cmd_validate
    )
    subparsers.add_parser("summary", help="one-page risk summary").set_defaults(
        func=cmd_summary
    )

    risks_parser = subparsers.add_parser("risks", help="list risks by priority")
    risks_parser.add_argument("--top", type=int, default=10, help="how many rows to show")
    risks_parser.set_defaults(func=cmd_risks)

    subparsers.add_parser("kri", help="show KRI status table").set_defaults(func=cmd_kri)

    subparsers.add_parser("report", help="write the Markdown executive report").set_defaults(
        func=cmd_report
    )
    subparsers.add_parser("dashboard", help="write the HTML dashboard").set_defaults(
        func=cmd_dashboard
    )

    challenge_parser = subparsers.add_parser(
        "challenge", help="list or play a risk-triage challenge"
    )
    challenge_parser.add_argument("--scenario", default=None, help="scenario id to play")
    challenge_parser.add_argument("--list", action="store_true", help="list scenarios")
    challenge_parser.add_argument(
        "--scenarios", default="scenarios", help="directory with scenario JSON files"
    )
    challenge_parser.add_argument(
        "--answers",
        default=None,
        help="batch answers, e.g. 'Q1=R-002;Q2=R-002,R-013' (skips interactive mode)",
    )
    challenge_parser.add_argument(
        "--show-solution", action="store_true", help="print answers and reasoning"
    )
    challenge_parser.set_defaults(func=cmd_challenge)

    ingest_parser = subparsers.add_parser(
        "ingest", help="validate and render lab findings linked to risks"
    )
    ingest_parser.add_argument(
        "--source",
        default="labs/findings.csv",
        help="lab findings CSV (default: labs/findings.csv; copy findings.sample.csv)",
    )
    ingest_parser.set_defaults(func=cmd_ingest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except DataError as exc:
        print(f"data error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"invalid data: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

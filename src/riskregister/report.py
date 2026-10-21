"""Markdown executive report generated from the risk register.

The report is the artefact a CISO actually reads: what the exposure is, where
it breaches the approved appetite, which indicators are off-target and what
is planned. It is generated deterministically from the CSV files so that it
can be attached to a committee pack and diffed between periods.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

from .models import KRI
from .registry import Registry
from .scales import LEVEL_EN, level, score

COMPANY = "Meridian Pay"
COMPANY_NOTE = "Fictional Brazilian fintech used as portfolio scenario"

STATUS_ICON = {"Verde": "🟢", "Amarelo": "🟡", "Vermelho": "🔴", "Sem dados": "⚪"}


def data_fingerprint(source_dir: str | Path) -> str:
    """SHA-256 over the data files - proves which version produced the report."""

    base = Path(source_dir)
    digest = hashlib.sha256()
    for path in sorted(base.glob("*.csv")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _fmt_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value or "-"


def _kri_row(kri: KRI) -> str:
    current = "-" if kri.current is None else f"{kri.current:g} {kri.unit}".strip()
    previous = "-" if kri.previous is None else f"{kri.previous:g}"
    trend = {"up": "▲", "down": "▼", "flat": "▬", "n/a": "-"}[kri.trend]
    return (
        f"| {kri.id} | {kri.name} | {STATUS_ICON[kri.status]} {kri.status} | "
        f"{current} | {previous} {trend} | {kri.owner} | {kri.frequency} |"
    )


def build_report(registry: Registry, generated_at: datetime | None = None) -> str:
    """Render the full executive report as a Markdown string."""

    now = generated_at or datetime.now(timezone.utc)
    appetites = registry.appetite_by_category
    breaches = registry.risks_above_appetite()
    issues = registry.validate()

    residual_scores = [risk.residual_score for risk in registry.risks]
    inherent_scores = [risk.inherent_score for risk in registry.risks]
    avg_residual = round(sum(residual_scores) / len(residual_scores), 1) if residual_scores else 0.0
    avg_inherent = round(sum(inherent_scores) / len(inherent_scores), 1) if inherent_scores else 0.0

    kri_counts = {"Verde": 0, "Amarelo": 0, "Vermelho": 0, "Sem dados": 0}
    for kri in registry.kris:
        kri_counts[kri.status] += 1

    critical_controls = [
        control for control in registry.controls if control.effectiveness == "Insuficiente"
    ]

    lines: list[str] = []
    add = lines.append

    add(f"# Relatorio Executivo de Risco - {COMPANY}")
    add("")
    add(f"> {COMPANY_NOTE}.")
    add("")
    add("| Campo | Valor |")
    add("|---|---|")
    add(f"| Data de geracao (UTC) | {now.strftime('%Y-%m-%d %H:%M')} |")
    add(f"| Data de referencia | {date.today().isoformat()} |")
    add(f"| Fingerprint dos dados (SHA-256) | `{data_fingerprint(registry.source_dir)}` |")
    add(f"| Riscos no registro | {len(registry.risks)} |")
    add(f"| Controles catalogados | {len(registry.controls)} |")
    add(f"| KRIs monitorados | {len(registry.kris)} |")
    add("")

    add("## 1. Sumario executivo")
    add("")
    add(
        f"- Score medio de risco **inherente**: {avg_inherent}/25 | "
        f"**residual**: {avg_residual}/25 "
        f"(-{round((avg_inherent - avg_residual) / avg_inherent * 100, 1) if avg_inherent else 0}%)."
    )
    add(
        f"- **{len(breaches)} risco(s) acima do apetite aprovado** "
        f"(severidade residual maior que a tolerada na categoria)."
    )
    add(
        f"- KRIs: {kri_counts['Verde']} verdes, {kri_counts['Amarelo']} amarelos, "
        f"{kri_counts['Vermelho']} vermelhos, {kri_counts['Sem dados']} sem dados."
    )
    if critical_controls:
        add(
            f"- **{len(critical_controls)} controle(s) com eficacia insuficiente** "
            "para sustentar o tratamento do risco."
        )
    if issues:
        add(f"- **{len(issues)} pendencia(s) de qualidade de dados** a corrigir (secao 7).")
    add("")

    add("## 2. Apetite de risco e status por categoria")
    add("")
    add("| Categoria | Apetite | Risco residual medio | Status |")
    add("|---|---|---|---|")
    for appetite in registry.appetites:
        category_risks = [r for r in registry.risks if r.appetite_ref == appetite.category]
        if category_risks:
            mean = round(sum(r.residual_score for r in category_risks) / len(category_risks), 1)
            mean_level = level(round(mean))
            breaching = sum(
                1
                for r in category_risks
                if LEVEL_EN[r.residual_level] and r.residual_level != "Baixo"
                and _rank(r.residual_level) > _rank(appetite.appetite_level)
            )
            status = f"🔴 {breaching} acima do apetite" if breaching else "🟢 Dentro do apetite"
            add(
                f"| {appetite.category} | {appetite.appetite_level} "
                f"({appetite.appetite_level_en}) | {mean} ({LEVEL_EN[mean_level]}) | {status} |"
            )
        else:
            add(f"| {appetite.category} | {appetite.appetite_level} | - | Sem riscos mapeados |")
    add("")

    add("## 3. Heat map de risco residual")
    add("")
    add("| Impacto \\ Probabilidade | 1 Raro | 2 Improvavel | 3 Possivel | 4 Provavel | 5 Quase certo |")
    add("|---|---|---|---|---|---|")
    for impact in (5, 4, 3, 2, 1):
        cells = []
        for likelihood in (1, 2, 3, 4, 5):
            hits = [
                risk
                for risk in registry.risks
                if risk.residual_likelihood == likelihood
                and risk.residual_impact == impact
            ]
            band = level(score(likelihood, impact))
            ids = ", ".join(r.id for r in hits) if hits else "-"
            cells.append(f"{LEVEL_EN[band]}: {ids}")
        add(f"| **{impact}** | " + " | ".join(cells) + " |")
    add("")

    add("## 4. Riscos prioritarios (top 10 por score residual)")
    add("")
    top = sorted(registry.risks, key=lambda r: r.priority_score, reverse=True)[:10]
    add(
        "| # | ID | Risco | Inerente | Residual | Owner | Tratamento | Prazo | Status |"
    )
    add("|---|---|---|---|---|---|---|---|---|")
    for index, risk in enumerate(top, start=1):
        add(
            f"| {index} | {risk.id} | {risk.title} | {risk.inherent_score} "
            f"({LEVEL_EN[risk.inherent_level]}) | **{risk.residual_score} "
            f"({LEVEL_EN[risk.residual_level]})** | {risk.owner} | {risk.treatment} | "
            f"{_fmt_date(risk.target_date)} | {risk.status} |"
        )
    add("")

    add("## 5. Riscos acima do apetite")
    add("")
    if breaches:
        add("| ID | Risco | Categoria | Residual | Apetite | Owner | Prazo |")
        add("|---|---|---|---|---|---|---|")
        for risk in breaches:
            appetite = appetites[risk.appetite_ref]
            add(
                f"| {risk.id} | {risk.title} | {risk.category} | "
                f"{risk.residual_score} ({LEVEL_EN[risk.residual_level]}) | "
                f"{appetite.appetite_level} | {risk.owner} | {_fmt_date(risk.target_date)} |"
            )
    else:
        add("Nenhum risco residual acima do apetite aprovado nesta periodo.")
    add("")

    add("## 6. Painel de KRIs")
    add("")
    add("| ID | Indicador | Status | Valor atual | Anterior | Owner | Frequencia |")
    add("|---|---|---|---|---|---|---|")
    for kri in sorted(registry.kris, key=lambda k: (k.status != "Vermelho", k.id)):
        add(_kri_row(kri))
    add("")

    add("## 7. Qualidade dos dados")
    add("")
    if issues:
        add("| # | Pendencia |")
        add("|---|---|")
        for index, issue in enumerate(issues, start=1):
            add(f"| {index} | {issue} |")
    else:
        add(
            "Nenhuma pendencia: referencias, escalas, limiares e vinculos entre "
            "riscos; controles e KRIs estao consistentes."
        )
    add("")

    add("## 8. Metodologia")
    add("")
    add(
        "- **Escala**: probabilidade x impacto 1-5, score = L x I (1-25). "
        "Faixas: 1-4 Baixo, 5-9 Moderado, 10-14 Alto, 15-25 Critico."
    )
    add(
        "- **Apetite**: nivel maximo aceito por categoria, aprovado por "
        "comite de risco. Qualquer risco residual acima do apetite exige "
        "aceitacao formal."
    )
    add(
        "- **KRIs**: limiares verde/ambar/vermelho por indicador, com direcao "
        "(`higher_is_better` / `lower_is_better`) e comparacao com o periodo anterior."
    )
    add(
        "- **Rastreabilidade**: fingerprint SHA-256 dos CSV de origem e "
        "versionado no GitHub; cada linha do registro aponta para controle, "
        "owner e prazo."
    )
    add("")

    return "\n".join(lines)


def _rank(level_name: str) -> int:
    order = {"Baixo": 1, "Moderado": 2, "Alto": 3, "Critico": 4}
    return order[level_name]

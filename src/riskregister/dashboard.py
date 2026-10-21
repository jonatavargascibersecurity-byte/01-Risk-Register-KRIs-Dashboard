"""Static HTML dashboard generator (no external dependencies).

The output is a single self-contained ``.html`` file: inline CSS, inline SVG
and a little vanilla JavaScript. It can be opened straight from disk, e-mailed
as an attachment or published with GitHub Pages - there is no server, no
build step and no CDN, which is exactly what an auditor wants to see.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .models import KRI, Risk
from .registry import Registry
from .report import data_fingerprint
from .scales import LEVEL_EN, level, score

COMPANY = "Meridian Pay"

BAND_COLORS = {
    "Baixo": "#2e7d32",
    "Moderado": "#f9a825",
    "Alto": "#ef6c00",
    "Critico": "#c62828",
}

STATUS_COLORS = {
    "Verde": "#2e7d32",
    "Amarelo": "#f9a825",
    "Vermelho": "#c62828",
    "Sem dados": "#9e9e9e",
}

CSS = """
:root { --bg:#f4f6f8; --card:#ffffff; --ink:#1b2430; --muted:#5c6b7a;
        --line:#dfe5ec; --accent:#0b5fff; }
* { box-sizing:border-box; }
body { margin:0; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
       background:var(--bg); color:var(--ink); }
header { background:linear-gradient(135deg,#0b1b3a,#0b5fff); color:#fff;
         padding:28px 32px; }
header h1 { margin:0 0 6px; font-size:24px; }
header p { margin:0; opacity:.85; font-size:14px; }
main { padding:24px 32px 48px; max-width:1200px; margin:0 auto; }
h2 { font-size:17px; margin:32px 0 12px; padding-bottom:8px;
     border-bottom:1px solid var(--line); }
.cards { display:flex; flex-wrap:wrap; gap:14px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:16px 18px; min-width:170px; flex:1; }
.card .label { font-size:12px; color:var(--muted); text-transform:uppercase;
               letter-spacing:.04em; }
.card .value { font-size:28px; font-weight:700; margin-top:6px; }
.card .sub { font-size:12px; color:var(--muted); margin-top:4px; }
table { width:100%; border-collapse:collapse; background:var(--card);
        border:1px solid var(--line); border-radius:10px; overflow:hidden; }
th,td { padding:9px 12px; text-align:left; font-size:13px;
        border-bottom:1px solid var(--line); vertical-align:top; }
th { background:#eef2f7; font-weight:600; color:#33414f; font-size:12px;
     text-transform:uppercase; letter-spacing:.03em; }
tr:last-child td { border-bottom:none; }
.pill { display:inline-block; padding:2px 9px; border-radius:999px;
        font-size:11px; font-weight:700; color:#fff; white-space:nowrap; }
.muted { color:var(--muted); }
.mono { font-family:Consolas,'Courier New',monospace; font-size:12px; }
.badge { display:inline-block; padding:2px 8px; border-radius:6px;
         background:#eef2f7; color:#33414f; font-size:11px; margin-right:4px; }
input[type=search] { padding:8px 12px; border:1px solid var(--line);
                      border-radius:8px; width:280px; font-size:13px; }
footer { color:var(--muted); font-size:12px; margin-top:32px;
         border-top:1px solid var(--line); padding-top:12px; }
.warn { background:#fff8e1; border:1px solid #ffe08a; border-radius:10px;
        padding:14px 16px; font-size:13px; }
"""

JS = """
function filterTable(inputId, tableId) {
  var q = document.getElementById(inputId).value.toLowerCase();
  var rows = document.querySelectorAll('#' + tableId + ' tbody tr');
  rows.forEach(function (row) {
    row.style.display = row.innerText.toLowerCase().indexOf(q) > -1 ? '' : 'none';
  });
}
"""


def _esc(value: object) -> str:
    return escape(str(value), quote=True)


def _kpi_card(label: str, value: object, sub: str = "") -> str:
    return (
        f'<div class="card"><div class="label">{_esc(label)}</div>'
        f'<div class="value">{_esc(value)}</div>'
        f'<div class="sub">{_esc(sub)}</div></div>'
    )


def _heat_map(registry: Registry) -> str:
    """Render the 5x5 residual heat map as inline SVG."""

    cell_w, cell_h = 118, 62
    left, top = 150, 24
    parts = [
        f'<svg viewBox="0 0 {left + 5 * cell_w + 20} {top + 5 * cell_h + 40}" '
        f'width="100%" style="max-width:760px" role="img" '
        f'aria-label="Heat map of residual risk">'
    ]

    for index in range(1, 6):
        x = left + (index - 1) * cell_w
        parts.append(
            f'<text x="{x + cell_w / 2}" y="16" text-anchor="middle" '
            f'font-size="12" fill="#5c6b7a">{index}</text>'
        )
        y = top + (5 - index) * cell_h
        parts.append(
            f'<text x="{left - 12}" y="{y + cell_h / 2 + 4}" text-anchor="end" '
            f'font-size="12" fill="#5c6b7a">{index}</text>'
        )

    for likelihood in range(1, 6):
        for impact in range(1, 6):
            x = left + (likelihood - 1) * cell_w
            y = top + (5 - impact) * cell_h
            band = level(score(likelihood, impact))
            hits = [
                risk
                for risk in registry.risks
                if risk.residual_likelihood == likelihood
                and risk.residual_impact == impact
            ]
            colour = BAND_COLORS[band]
            parts.append(
                f'<rect x="{x + 1}" y="{y + 1}" width="{cell_w - 2}" '
                f'height="{cell_h - 2}" rx="6" fill="{colour}" fill-opacity="0.85" '
                f'stroke="#ffffff" stroke-width="2"/>'
            )
            label = ", ".join(r.id for r in hits[:4]) + (
                f" +{len(hits) - 4}" if len(hits) > 4 else ""
            )
            if hits:
                parts.append(
                    f'<text x="{x + cell_w / 2}" y="{y + 26}" text-anchor="middle" '
                    f'font-size="12" fill="#ffffff" font-weight="700">{len(hits)}</text>'
                )
                parts.append(
                    f'<text x="{x + cell_w / 2}" y="{y + 44}" text-anchor="middle" '
                    f'font-size="10" fill="#ffffff">{_esc(label)}</text>'
                )
            else:
                parts.append(
                    f'<text x="{x + cell_w / 2}" y="{y + cell_h / 2 + 4}" '
                    f'text-anchor="middle" font-size="11" fill="#ffffff" '
                    f'fill-opacity="0.65">-</text>'
                )

    parts.append(
        f'<text x="{left}" y="{top + 5 * cell_h + 26}" font-size="11" fill="#5c6b7a">'
        "Eixo X: probabilidade (1-5) &#183; Eixo Y: impacto (1-5) &#183; "
        "score = L x I &#183; cores = faixa de severidade residual</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def _kri_row(kri: KRI) -> str:
    current = "-" if kri.current is None else f"{kri.current:g} {kri.unit}".strip()
    previous = "-" if kri.previous is None else f"{kri.previous:g}"
    arrow = {"up": "&#9650;", "down": "&#9660;", "flat": "&#9644;", "n/a": "-"}[kri.trend]
    return (
        f"<tr><td class='mono'>{_esc(kri.id)}</td><td>{_esc(kri.name)}</td>"
        f"<td><span class='pill' style='background:{STATUS_COLORS[kri.status]}'>"
        f"{_esc(kri.status)}</span></td>"
        f"<td>{_esc(current)}</td><td class='muted'>{_esc(previous)} {arrow}</td>"
        f"<td>{_esc(kri.owner)}</td>"
        f"<td class='muted'>{_esc(kri.linked_risks and ', '.join(kri.linked_risks) or '-')}</td>"
        f"</tr>"
    )


def _risk_row(risk: Risk, appetite_level: str | None) -> str:
    colour = BAND_COLORS[risk.residual_level]
    appetite_tag = ""
    if appetite_level and _rank(risk.residual_level) > _rank(appetite_level):
        appetite_tag = " <span class='badge' style='background:#fdecea'>acima do apetite</span>"
    return (
        f"<tr><td class='mono'>{_esc(risk.id)}</td><td>{_esc(risk.title)}</td>"
        f"<td>{_esc(risk.category)}</td>"
        f"<td><span class='pill' style='background:{colour}'>"
        f"{risk.residual_score} &#183; {LEVEL_EN[risk.residual_level]}</span></td>"
        f"<td class='muted'>{risk.inherent_score} &#8594; {risk.residual_score} "
        f"(-{risk.reduction_pct}%)</td>"
        f"<td>{_esc(risk.owner)}{appetite_tag}</td>"
        f"<td>{_esc(risk.treatment)}</td>"
        f"<td class='muted'>{_esc(risk.target_date)}</td>"
        f"<td class='muted'>{_esc(risk.status)}</td></tr>"
    )


def _rank(level_name: str) -> int:
    return {"Baixo": 1, "Moderado": 2, "Alto": 3, "Critico": 4}[level_name]


def build_dashboard(registry: Registry, generated_at: datetime | None = None) -> str:
    """Render the complete dashboard as a self-contained HTML document."""

    now = generated_at or datetime.now(timezone.utc)
    appetites = registry.appetite_by_category
    breaches = registry.risks_above_appetite()
    issues = registry.validate()

    kri_counts = {"Verde": 0, "Amarelo": 0, "Vermelho": 0, "Sem dados": 0}
    for kri in registry.kris:
        kri_counts[kri.status] += 1

    avg_residual = (
        round(sum(r.residual_score for r in registry.risks) / len(registry.risks), 1)
        if registry.risks
        else 0.0
    )
    top = sorted(registry.risks, key=lambda r: r.priority_score, reverse=True)[:12]

    ineffective = [c for c in registry.controls if c.effectiveness == "Insuficiente"]

    html: list[str] = []
    add = html.append

    add("<!DOCTYPE html>")
    add("<html lang='pt-BR'>")
    add("<head>")
    add("<meta charset='utf-8'>")
    add("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    add(f"<title>Risk Dashboard - {COMPANY}</title>")
    add(f"<style>{CSS}</style>")
    add("</head>")
    add("<body>")
    add(
        f"<header><h1>Risk &amp; KRI Dashboard - {COMPANY}</h1>"
        "<p>GRC portfolio project - fictional Brazilian fintech scenario "
        f"&#183; generated {now.strftime('%Y-%m-%d %H:%M UTC')}</p></header>"
    )
    add("<main>")

    add("<div class='cards'>")
    add(_kpi_card("Riscos no registro", len(registry.risks), "entradas ativas"))
    add(_kpi_card("Acima do apetite", len(breaches), "exigem aceitacao formal"))
    add(_kpi_card("Score residual medio", f"{avg_residual}/25", "limite maximo 25"))
    add(_kpi_card("KRIs fora do alvo", kri_counts["Vermelho"], "status vermelho"))
    add(_kpi_card("Controles", len(registry.controls), f"{len(ineffective)} insuficientes"))
    add("</div>")

    add("<h2>1. Heat map de risco residual / Residual risk heat map</h2>")
    add(_heat_map(registry))

    add("<h2>2. Riscos priorizados / Prioritised risks</h2>")
    add("<input type='search' id='riskSearch' placeholder='Filtrar risco, categoria, owner...'>")
    add("<table id='riskTable'><thead><tr><th>ID</th><th>Risco</th><th>Categoria</th>"
        "<th>Residual</th><th>Inerente &#8594; Residual</th><th>Owner</th>"
        "<th>Tratamento</th><th>Prazo</th><th>Status</th></tr></thead><tbody>")
    for risk in top:
        appetite = appetites.get(risk.appetite_ref)
        add(_risk_row(risk, appetite.appetite_level if appetite else None))
    add("</tbody></table>")

    add("<h2>3. Painel de KRIs / KRI dashboard</h2>")
    add("<div class='cards'>")
    for status in ("Verde", "Amarelo", "Vermelho", "Sem dados"):
        add(_kpi_card(status, kri_counts[status], "indicadores"))
    add("</div>")
    add("<br>")
    add("<table id='kriTable'><thead><tr><th>ID</th><th>Indicador</th><th>Status</th>"
        "<th>Valor atual</th><th>Anterior</th><th>Owner</th><th>Riscos vinculados</th>"
        "</tr></thead><tbody>")
    for kri in sorted(registry.kris, key=lambda k: (k.status != "Vermelho", k.id)):
        add(_kri_row(kri))
    add("</tbody></table>")

    add("<h2>4. Apetite de risco por categoria / Risk appetite</h2>")
    add("<table><thead><tr><th>Categoria</th><th>Apetite</th><th>Tolerancia</th>"
        "<th>Aprovado por</th><th>Desde</th></tr></thead><tbody>")
    for appetite in registry.appetites:
        add(
            f"<tr><td>{_esc(appetite.category)}</td>"
            f"<td><span class='pill' style='background:{BAND_COLORS.get(appetite.appetite_level, '#5c6b7a')}'>"
            f"{_esc(appetite.appetite_level)}</span></td>"
            f"<td>{_esc(appetite.tolerance)}</td>"
            f"<td>{_esc(appetite.approved_by)}</td>"
            f"<td class='muted'>{_esc(appetite.approved_on)}</td></tr>"
        )
    add("</tbody></table>")

    add("<h2>5. Qualidade dos dados / Data quality</h2>")
    if issues:
        add("<div class='warn'><strong>")
        add(str(len(issues)))
        add("</strong> pendencia(s) de qualidade de dados encontradas:<ul>")
        for issue in issues:
            add(f"<li>{_esc(issue)}</li>")
        add("</ul></div>")
    else:
        add(
            "<div class='warn' style='background:#edf7ed;border-color:#b7e0b7'>"
            "<strong>Sem pendencias.</strong> Referencias, escalas, limiares de KRI "
            "e vinculos entre riscos; controles e KRIs estao consistentes.</div>"
        )

    add(
        f"<footer>Fingerprint dos dados (SHA-256): "
        f"<span class='mono'>{data_fingerprint(registry.source_dir)}</span> "
        "&#183; gerado por <span class='mono'>python -m riskregister dashboard</span> "
        "&#183; projeto de portfolio, cenario ficticio.</footer>"
    )
    add("</main>")
    add(f"<script>{JS}</script>")
    add("<script>document.getElementById('riskSearch')"
        ".addEventListener('input',function(){filterTable('riskSearch','riskTable')});</script>")
    add("</body>")
    add("</html>")
    return "\n".join(html)


def write_dashboard(registry: Registry, output: str | Path) -> Path:
    """Render and write the dashboard to *output*; returns the written path."""

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_dashboard(registry), encoding="utf-8")
    return path

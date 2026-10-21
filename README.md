# Risk Register + KRI Dashboard

A small, dependency-free **GRC (Governance, Risk & Compliance)** toolkit that turns a plain CSV risk register into the artefacts a risk committee actually reads:

- a **prioritised risk register** with inherent vs. residual scoring,
- a **KRI (Key Risk Indicator) dashboard** with green/amber/red thresholds,
- an **executive risk report** (Markdown),
- a **self-contained HTML dashboard** (heat map + tables, no CDN, no server).

It is built around a fictional Brazilian fintech, **Meridian Pay**, so the scenario is realistic (LGPD, PCI-DSS, DORA, PIX, ransomware, third parties) without exposing any real organisation.

> This is a **portfolio project for entry-level cybersecurity / GRC roles**. It demonstrates risk scoring methodology (ISO 31000 / NIST RMF style 5x5 matrix), risk appetite, control effectiveness, KRI monitoring and evidence-driven reporting.

## Why this project

Entry-level GRC jobs ask for candidates who can: build a risk register, score it consistently, compare it against risk appetite, monitor KRIs and report to non-technical stakeholders. This repo does all of it from data, and every number is computed - nothing is hard-coded into the dashboard.

## Features

| Feature | Description |
|---|---|
| **5x5 scoring** | Likelihood x Impact (1-25), four severity bands (`Baixo` -> `Critico`) |
| **Inherent vs residual** | Each risk carries both, plus the % reduction from controls |
| **Risk appetite** | Per-category appetite; flags every risk above the approved tolerance |
| **Control catalog** | 18 controls with framework refs (ISO 27001 Annex A, NIST CSF, PCI-DSS) and effectiveness |
| **KRI engine** | 12 indicators with direction, thresholds and period-over-period trend |
| **Data quality checks** | Broken references, orphan controls, invalid scales, bad thresholds, stale KRI links |
| **Reports** | Markdown executive report + HTML dashboard, both generated deterministically |
| **Reproducibility** | SHA-256 fingerprint of the source CSV files printed in every report |

## Quick start

```bash
cd 01-Risk-Register-KRIs-Dashboard
pip install -e ".[dev]"          # or just run with PYTHONPATH=src on Python 3.10+

python -m riskregister validate  # data quality checks
python -m riskregister summary   # one-page summary
python -m riskregister risks --top 10
python -m riskregister kri
python -m riskregister report    --out build
python -m riskregister dashboard --out build
```

Then open `build/dashboard.html` in any browser.

No third-party runtime dependencies - only the Python standard library.

## Example output

```
RISK REGISTER SUMMARY
Risks registered        : 16
Above approved appetite : 7
Average residual score  : 9.2/25
Controls catalogued     : 18
KRIs monitored          : 12
KRI status              : 1 green / 9 amber / 2 red / 0 no data
```

## Repository layout

```
01-Risk-Register-KRIs-Dashboard/
├── data/                    # single source of truth (CSV)
│   ├── risks.csv            # risk register
│   ├── controls.csv         # control catalog
│   ├── kris.csv             # key risk indicators
│   └── risk_appetite.csv    # approved appetite per category
├── src/riskregister/
│   ├── scales.py            # scoring model (5x5, bands, appetite)
│   ├── models.py            # Risk / Control / KRI / Appetite
│   ├── registry.py          # loading, validation, saving
│   ├── report.py            # Markdown executive report
│   ├── dashboard.py         # self-contained HTML dashboard (inline SVG)
│   └── cli.py               # command line interface
├── tests/                   # unit + integration tests
└── build/                   # generated artefacts (git-ignored)
```

## Methodology

- **Score** = Likelihood (1-5) x Impact (1-5). Bands: 1-4 Low, 5-9 Moderate, 10-14 High, 15-25 Critical.
- **Risk appetite**: maximum accepted level per category, approved by the risk committee. A residual risk above appetite requires formal acceptance.
- **KRIs**: each indicator has a direction (`higher_is_better` / `lower_is_better`) and thresholds (`green` / `amber` / `red`), evaluated against the current and previous values.
- **Traceability**: every risk points to controls, an owner, a treatment plan, a target date and a review date.

## Tests

```bash
python -m pytest
```

## License

MIT

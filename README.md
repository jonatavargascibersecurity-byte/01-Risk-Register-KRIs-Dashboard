# Registro de Riscos + Dashboard de KRIs

Toolkit de **GRC (Governança, Risco e Conformidade)** sem dependências que transforma um registro de riscos em CSV nos artefatos que um comitê de risco realmente lê:

- um **registro de riscos priorizado**, com score inerente vs. residual,
- um **painel de KRIs** (Indicadores-Chave de Risco) com limiares verde/amarelo/vermelho,
- um **relatório executivo de risco** (Markdown),
- um **dashboard HTML autocontido** (heat map + tabelas, sem CDN, sem servidor).

O cenário é uma fintech brasileira fictícia, **Meridian Pay**, realista (LGPD, PCI-DSS, DORA, PIX, ransomware, terceiros) sem expor nenhuma organização real.

> Este é um **projeto de portfólio para vagas de entrada em cibersegurança / GRC**. Demonstra metodologia de scoring de risco (matriz 5x5 estilo ISO 31000 / NIST RMF), apetite de risco, eficácia de controles, monitoramento de KRIs e reporte orientado a evidências.

## Por que este projeto

Vagas de GRC de entrada pedem candidatos que saibam: construir um registro de riscos, pontuá-lo de forma consistente, compará-lo ao apetite de risco, monitorar KRIs e reportar para partes interessadas não técnicas. Este repositório faz tudo isso a partir de dados, e cada número é calculado - nada é fixo no dashboard.

## Funcionalidades

| Recurso | Descrição |
|---|---|
| **Scoring 5x5** | Probabilidade x Impacto (1-25), quatro faixas de severidade (`Baixo` -> `Critico`) |
| **Inerente vs residual** | Cada risco carrega os dois, mais o % de redução obtido pelos controles |
| **Apetite de risco** | Apetite por categoria; sinaliza todo risco acima da tolerância aprovada |
| **Catálogo de controles** | 18 controles com referências de framework (ISO 27001 Anexo A, NIST CSF, PCI-DSS) e eficácia |
| **Motor de KRIs** | 12 indicadores com direção, limiares e tendência período a período |
| **Verificações de qualidade** | Referências quebradas, controles órfãos, escalas inválidas, limiares errados, vínculos obsoletos |
| **Relatórios** | Relatório executivo em Markdown + dashboard HTML, ambos derivados do mesmo CSV e identificados pelo fingerprint SHA-256 |
| **Reprodutibilidade** | Fingerprint SHA-256 dos CSV de origem impresso em todo relatório |

## Início rápido

```bash
cd 01-Risk-Register-KRIs-Dashboard
pip install -e ".[dev]"          # ou rode com PYTHONPATH=src no Python 3.10+

python -m riskregister validate  # checagens de qualidade de dados
python -m riskregister summary   # resumo de uma página
python -m riskregister risks --top 10
python -m riskregister kri
python -m riskregister --out build report
python -m riskregister --out build dashboard
python -m riskregister challenge --list
python -m riskregister --out build challenge --scenario risk-triage-thm --show-solution
```

Abra `build/dashboard.html` em qualquer navegador.

Sem dependências de terceiros em tempo de execução - apenas a biblioteca padrão do Python.

## Alinhamento com plataformas de estudo

Este repositório é um laboratório de prática para trilhas de GRC e defesa. Cada sala/trilha vira uma melhoria rastreável; o mapeamento completo (plataforma, link, artefato e o que foi resolvido) está em [`PLATFORMS.md`](PLATFORMS.md).

| Plataforma / trilha | Link | Como o repositório aplica |
|---|---|---|
| TryHackMe - Governance & Regulation | [sala](https://tryhackme.com/room/cybergovernanceregulation) | Apetite por categoria, priorização por risco residual e relatório orientado a evidências. Cenário `risk-triage-thm`. |
| TryHackMe - Threats & Risks | [módulo](https://tryhackme.com/module/threats-and-risks) | Ciclo identificar → avaliar → responder → monitorar exercitado no comando `challenge`. |
| LetsDefend - SOC Manager Path | [trilha](https://app.letsdefend.io/training) | Triage e escalonamento viram perguntas de KRI no cenário `kri-monitoring-letsdefend`. |
| HTB Academy - SOC Analyst Path | [trilha](https://academy.hackthebox.com/path/preview/soc-analyst) | Estrutura de relatório com evidências e KRIs operacionais. |
| HTB - Governance & Compliance | [recursos](https://www.hackthebox.com/cybersecurity-resources/governance_compliance) | DORA/NIST CSF 2.0 no catálogo de controles e no crosswalk do repositório 02. |

### Modo desafio

```bash
python -m riskregister challenge --list
python -m riskregister challenge --scenario risk-triage-thm
python -m riskregister --out build challenge --scenario risk-triage-thm --show-solution
```

As respostas são calculadas do próprio CSV (`data/risks.csv`, `data/kris.csv`), então o exercício nunca divergiu do registro.

### Ingestão de achados de laboratório

Copie `labs/findings.sample.csv` para `labs/findings.csv`, registre uma linha por sala e rode:

```bash
python -m riskregister --out build ingest --source labs/findings.csv
```

O comando valida se o `risk_id` existe e gera `build/lab-findings.md` com o link da sala, o risco e **como o problema foi resolvido**. Use o template em [`learning-log/000-template.md`](learning-log/000-template.md) para o write-up.

## Layout do repositório

```
01-Risk-Register-KRIs-Dashboard/
├── data/                    # fonte única da verdade (CSV)
│   ├── risks.csv            # registro de riscos
│   ├── controls.csv         # catálogo de controles
│   ├── kris.csv             # indicadores-chave de risco
│   └── risk_appetite.csv    # apetite aprovado por categoria
├── src/riskregister/
│   ├── scales.py            # modelo de scoring (5x5, faixas, apetite)
│   ├── models.py            # Risk / Control / KRI / Appetite
│   ├── registry.py          # carga, validação, gravação
│   ├── report.py            # relatório executivo em Markdown
│   ├── dashboard.py         # dashboard HTML autocontido (SVG inline)
│   ├── challenge.py         # cenários jogáveis (respostas calculadas do CSV)
│   ├── ingest.py            # achados de laboratório -> registro de riscos
│   └── cli.py               # interface de linha de comando
├── scenarios/               # cenários JSON com link da plataforma
├── labs/                    # findings.sample.csv (copie para findings.csv)
├── learning-log/            # template de write-up por sala/trilha
├── tests/                   # testes unitários + de integração
└── build/                   # artefatos gerados (ignorados pelo git)
```

## Metodologia

- **Score** = Probabilidade (1-5) x Impacto (1-5). Faixas: 1-4 Baixo, 5-9 Moderado, 10-14 Alto, 15-25 Crítico.
- **Apetite de risco**: nível máximo aceito por categoria, aprovado pelo comitê de risco. Risco residual acima do apetite exige aceitação formal.
- **KRIs**: cada indicador tem direção (`higher_is_better` / `lower_is_better`) e limiares (`green` / `amber` / `red`), avaliados contra o valor atual e o anterior.
- **Rastreabilidade**: cada risco aponta para controles, responsável, plano de tratamento, prazo e data de revisão.

## Testes

```bash
python -m pytest
```

## Licença

MIT

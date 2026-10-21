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
| **Relatórios** | Relatório executivo em Markdown + dashboard HTML, ambos gerados de forma determinística |
| **Reprodutibilidade** | Fingerprint SHA-256 dos CSV de origem impresso em todo relatório |

## Início rápido

```bash
cd 01-Risk-Register-KRIs-Dashboard
pip install -e ".[dev]"          # ou rode com PYTHONPATH=src no Python 3.10+

python -m riskregister validate  # checagens de qualidade de dados
python -m riskregister summary   # resumo de uma página
python -m riskregister risks --top 10
python -m riskregister kri
python -m riskregister report    --out build
python -m riskregister dashboard --out build
```

Abra `build/dashboard.html` em qualquer navegador.

Sem dependências de terceiros em tempo de execução - apenas a biblioteca padrão do Python.

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
│   └── cli.py               # interface de linha de comando
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

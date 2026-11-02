# Plataformas, trilhas e como este repositório se conecta

Este repositório foi pensado para gerar **evidência prática** ao estudar em trilhas de GRC/Defensiva. A regra é: *1 sala/trilha = 1 melhoria commitada, com menção ao que foi resolvido*.

## Mapeamento direto

| Plataforma / Trilha / Sala | Foco | Como este repo se relaciona | Como foi/será aplicado |
|---|---|---|---|
| [TryHackMe - Governance & Regulation](https://tryhackme.com/room/cybergovernanceregulation) | Governança, leis/regulamentos, GRC framework | Casamento direto com o modelo de governança, apetite de risco e reporte executivo. | Usar o registro de riscos para mapear componentes do framework GRC (Governança/Risco/Conformidade) e documentar decisões no relatório. |
| [TryHackMe - Threats & Risks (Risk Management)](https://tryhackme.com/module/threats-and-risks) | Identificar/avaliar/responder/monitorar riscos | Scoring 5x5, apetite, KRIs com thresholds e priorização. | Aplicar o ciclo `Identify → Assess → Respond → Monitor` aos riscos reais do CSV e justificar priorização com base em `residual_score` e apetite. |
| [LetsDefend - SOC Manager Path](https://app.letsdefend.io/training) | Triage, avaliação, escalonamento, documentação | Gera artefatos prontos para reporte (executivo + dashboard). | Transformar lições de triage em entradas do registro (cenários, tratamentos) e usar o formato de relatório para incidentes simulados. |
| [HTB Academy - SOC Analyst Path](https://academy.hackthebox.com/path/preview/soc-analyst) | Detecção/forense/relatórios | Relatórios seguem estrutura próxima a "Security Incident Reporting". | Adaptar relatório executivo para incluir timeline, evidências, impacto e recomendações - alinhado ao módulo de incident reporting. |
| [HTB - Governance & Compliance](https://www.hackthebox.com/cybersecurity-resources/governance_compliance) | DORA, NIST CSF 2.0, PCI-DSS | Base para enriquecer mapeamentos entre frameworks. | Cruzar controles/requisitos com os riscos/KRIs e registrar gaps no contexto de regulamentações aplicáveis. |

## Como usar para benefício duplo

1. Estude a sala/trilha na plataforma
2. Identifique um conceito que pode virar melhoria no repo (cenário, métrica KRI, threshold, regra de validação)
3. Implemente no código/dados, gere artefatos (`report`, `dashboard`)
4. **Commit com mensagem clara**: `feat: add scenario from TryHackMe Governance&Regulation (Room: https://...) - links R-XXX to exercise resolution`
5. Atualize este arquivo com o link do commit/sala resolvida

## Status de alinhamento

- [x] Estrutura base (risks/controls/kris/appetite) alinhada a Risk Management
- [x] `scenarios/` + comando `challenge` (Fase 2) - respostas calculadas do CSV
- [x] `ingest` para achados de laboratório + template em `learning-log/` (Fases 5-6)
- [ ] Metadados do GitHub (description/topics) atualizados via `gh repo edit`

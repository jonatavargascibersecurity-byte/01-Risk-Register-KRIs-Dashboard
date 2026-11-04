# Plataformas, trilhas e como este repositório se conecta

Este repositório foi pensado para gerar **evidência prática** ao estudar em trilhas de GRC/Defensiva. A regra é: *1 sala/trilha = 1 melhoria commitada, com menção ao que foi resolvido*.

## Mapeamento direto

| Plataforma / Trilha / Sala | Foco | Como este repo se relaciona | Como foi aplicado (evidência) |
|---|---|---|---|
| [TryHackMe - Governance & Regulation](https://tryhackme.com/room/cybergovernanceregulation) | Governança, leis/regulamentos, GRC framework | Casamento direto com o modelo de governança, apetite de risco e reporte executivo. | Cenário `risk-triage-thm` (`scenarios/risk-triage-thm.json`) responde apetite por categoria e priorização por residual; achado `LF-001` em `labs/findings.sample.csv` registra a sala e o artefato. |
| [TryHackMe - Risk Management](https://tryhackme.com/room/seriskmanagement) | Identificar/avaliar/responder/monitorar riscos | Scoring 5x5, apetite, KRIs com thresholds e priorização. | O comando `challenge` aplica `Identify → Assess → Respond → Monitor` sobre o CSV real e justifica a ordem com `residual_score` + apetite (Q1/Q2/Q6). |
| [LetsDefend - Incident Triage, Assessment and Escalation](https://app.letsdefend.io/training/lessons/incident-triage-assessment-and-escalation) | Triage, avaliação, escalonamento, documentação | Gera artefatos prontos para reporte (executivo + dashboard). | Cenário `kri-monitoring-letsdefend` cobre thresholds/KRIs; achado `LF-002` liga o curso ao risco `R-003` e ao artefato gerado. |
| [HTB Academy - Security Incident Reporting](https://academy.hackthebox.com/course/preview/security-incident-reporting) | Detecção/forense/relatórios | Relatórios seguem estrutura de incident report. | Achado `LF-003` liga o módulo a `R-002`; `report`/`dashboard` registram tratamento, dono, prazo e status por risco. |
| [HTB Academy - Information Security Guidelines](https://academy.hackthebox.com/course/preview/information-security-guidelines) | Governança, DORA, NIST CSF 2.0, PCI-DSS | Base para enriquecer mapeamentos entre frameworks. | O crosswalk ISO Anexo A → SOC 2 / NIST CSF 2.0 / DORA / LGPD é gerado no repositório 02 e serve de vocabulário para os `framework_ref` dos controles deste registro. |

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
- [x] Metadados do GitHub (description/topics) atualizados via API: *Risk register + KRI dashboard in pure Python/CSV with playable TryHackMe/LetsDefend challenges and lab-findings ingest*; topics `grc`, `risk-management`, `kri`, `iso-27001`, `nist-csf`, `dora`, `lgpd`, `tryhackme`, `letsdefend`, `hackthebox`, `python`, `portfolio`

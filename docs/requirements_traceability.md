# Matriz de rastreabilidade

Esta matriz liga os requisitos implementados às superfícies de código e aos
testes automatizados. Os resultados são sintéticos e não substituem validação
com participantes.

| Requisito | Implementação | Evidência automatizada |
|---|---|---|
| Separar estado verdadeiro, observação e avaliação | `environment.py`, `controller.py` | `tests/test_controller.py`, `tests/test_runner.py` |
| Usar vocabulário fechado de ações | `uxagent_actions.py`, `uxagent_action.schema.json` | `tests/test_action_schema.py` |
| Impedir atribuições incompatíveis | `controller.py` | `tests/test_controller.py`, `tests/test_mechanisms.py` |
| Exigir revisão antes da confirmação | `controller.py`, `environment.py` | `tests/test_controller.py`, `tests/test_session.py` |
| Representar T1 sem ações exclusivas de T2 | `controller.py` | `tests/test_session.py` |
| Atualizar feed explicitamente em T2 | `environment.py`, `controller.py`, `uxagent_session.py` | `tests/test_session.py`, `tests/test_runner.py` |
| Controlar comunicação por `send_ping` | `controller.py`, `mechanisms.py` | `tests/test_mechanisms.py` |
| Disponibilizar checklist e ajuda contextual | `controller.py`, `uxagent_session.py`, `uxagent_web.py` | `tests/test_mechanisms.py`, `tests/test_web.py` |
| Manter contrato estável entre backend e interface | `uxagent_ui.schema.json`, `uxagent_session.py` | `tests/test_session.py`, `tests/test_web.py` |
| Registrar eventos auditáveis em JSONL | `event_logger.py`, `uxagent_event.schema.json` | `tests/test_event_schema.py`, `tests/test_runner.py` |
| Registrar rejeições sem quebrar a sessão | `event_logger.py`, `controller.py` | `tests/test_event_schema.py`, `tests/test_session.py` |
| Avaliar pelo estado verdadeiro | `environment.py`, `uxagent_session.py` | `tests/test_session.py`, `tests/test_web.py` |
| Integrar política Gemini com validação local | `gemini_client.py`, `uxagent_cli.py` | smoke tests reais T1/T2; suíte automatizada cobre os contratos |
| Reproduzir mecanismos R1--R4 | `mechanisms.py`, `config_diagnostica_R2_R3_R4.json` | `tests/test_mechanisms.py`, `tests/test_runner.py` |
| Executar T3 com replanejamento independente | `environment.py`, `controller.py`, `uxagent_session.py` | `tests/test_reserved_tasks.py` |
| Executar T4 com integração de painéis | `environment.py`, `controller.py`, `uxagent_session.py` | `tests/test_reserved_tasks.py` |
| Formalizar HTA, CTT, GOMS/KLM e MoLIC | `docs/ihc_design_artifacts_v1.md` | inspeção documental |
| Definir protocolo, tolerâncias e ética | `docs/human_validation_protocol_v1.md` | revisão antes de coleta |
| Auditar entregáveis e rubrica P3 | `docs/uxagent_p3_report.tex` | auditoria documental; lacunas explicitadas |
| Formalizar CTT, MoLIC e matriz MAC | `docs/design_specification_e1.md` | caderno E1 complementar |
| Produzir pacote E3 reproduzível | `pilot_e3.zip`, `tools/run_pilot.py` | seis sessões mock e duas sessões Gemini rastreadas |
| Preparar demonstração | `docs/demo_script_3_to_5_min.md` | roteiro reproduzível; vídeo ainda não gravado |
| Preparar aprovação institucional | `docs/institutional_review_checklist.md` | checklist; aprovação ainda pendente |

## Evidência Gemini em 2026-11-05

- T1 real: sucesso em 5 propostas.
- T2 real: sucesso em 18 propostas na primeira execução completa.
- T2 real após reforço do prompt: sucesso em 13 propostas.
- Em ambas as execuções T2, repetições de `send_ping` foram rejeitadas pelo
  controlador e registradas no log; não produziram efeito indevido.
- O log T2 validado continha 76 eventos e zero violações do schema.

Esses resultados demonstram integração e robustez do controlador, mas não
medem qualidade humana, usabilidade ou desempenho geral do modelo.

## Estado após o congelamento técnico

- T3/T4 têm implementação independente e continuam reservadas para validação;
  seus resultados não calibram T1/T2.
- Interface, prompt, configuração, schemas e modelo estão congelados para a
  base técnica em [`freeze_manifest_v6.json`](freeze_manifest_v6.json).
- O congelamento técnico não autoriza estudo humano nem transforma resultados
  sintéticos em evidência empírica.
- O protocolo, a amostra operacional, as tolerâncias e a ética estão
  documentados, mas aprovação institucional e recrutamento ainda não ocorreram.
- A auditoria final dos artefatos contra a interface concreta ainda deve ser
  conduzida em piloto técnico.

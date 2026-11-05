# Revisão do repositório contra a documentação oficial

**Data:** 2026-11-05  
**Escopo:** `EnunciadoUXAgent.pdf`, `HTSAgent-A2.pdf`,
`Modelagem__IHC_.pdf`, `UXAgentDesign-A3.pdf` e
`Tarefas_validacao_reservadas_v2.md`.

## Resumo executivo

O repositório está tecnicamente consistente para calibração sintética de T1/T2,
teste do controlador, validação do contrato de eventos e prototipação web de
baixa fidelidade. A separação entre ambiente, observação, política, controlador,
instrumentação e avaliador externo está implementada.

Ele **ainda não está aprovado como entrega final de Design UXAgent**. Os
artefatos formais de IHC estão documentados e foram auditados contra o
protótipo; validação humana e aprovação institucional continuam pendentes.

## Conformidade por requisito

| Área | Estado | Evidência | Observação |
|---|---|---|---|
| Separação estado verdadeiro/observação | Atendido | `environment.py`, `controller.py` | O avaliador usa o estado verdadeiro. |
| Vocabulário fechado e schemas | Atendido | `uxagent_action.schema.json`, `uxagent_ui.schema.json` | Ações e modelo visual são validados localmente. |
| Mecanismos externos ao prompt | Atendido | `mechanisms.py`, `controller.py` | R1--R4 são parametrizados e desligados por padrão. |
| T1/T2 de calibração | Atendido | `environment.py`, `tests/` | Há execução mock e integração real Gemini testada. |
| Instrumentação e eventos | Atendido | `event_logger.py`, `uxagent_event.schema.json` | Eventos JSONL são validados na escrita. |
| Avaliação independente | Atendido | `environment.py`, `uxagent_session.py` | O resultado não é decidido pelo Gemini. |
| Interface instrumentada | Atendido como protótipo | `uxagent_web.py`, `uxagent_session.py` | Protótipo web funcional com refinamento visual; ainda não é produto final. |
| Quatro tarefas, duas reservadas | Atendido tecnicamente | `environment.py`, `tests/test_reserved_tasks.py` | T1/T2 calibram; T3/T4 executam em versão independente e continuam reservadas. |
| HTA | Atendido como artefato | `docs/ihc_design_artifacts_v1.md` | HTA refinada registrada sem entregar o modelo ao agente. |
| CTT | Atendido como artefato | `docs/ihc_design_artifacts_v1.md` | CTT textual versionado. |
| GOMS/KLM | Atendido como hipótese | `docs/ihc_design_artifacts_v1.md` | Contagens documentadas; não são tempos humanos. |
| MoLIC e rupturas | Atendido como artefato | `docs/ihc_design_artifacts_v1.md` | Cenas, falas, transições e recuperações registradas. |
| Metamensagem e signos | Atendido como artefato | `docs/ihc_design_artifacts_v1.md` | Canais e fronteira de informação explicitados. |
| Protocolo humano/ética | Base documentada | `docs/human_validation_protocol_v1.md` | Plano e limites registrados; aprovação institucional ainda não existe. |
| Validação independente T3/T4 | Reservado | `Tarefas_validacao_reservadas_v2.md` | Não usar para calibrar prompts, mecanismos ou interface. |

## Decisões de congelamento

Foi congelada a base técnica atual para reprodutibilidade, conforme
[`freeze_manifest_v4.json`](freeze_manifest_v4.json). A partir deste ponto:

1. alterações em interface, prompt, mecanismos, schemas, avaliador ou modelo
   invalidam a base congelada e exigem nova versão;
2. T3/T4 continuam independentes e não podem orientar ajustes de T1/T2;
3. resultados Gemini e mock continuam sintéticos;
4. o congelamento não significa que a entrega final de IHC esteja aprovada.

## Evidência executada

- Suíte automatizada: **70 testes aprovados**.
- Compilação: aprovada.
- Verificação de whitespace: aprovada.
- Gemini T1: sucesso em 5 propostas.
- Gemini T2: sucesso em 18 propostas e, após reforço do prompt, em 13 propostas.
- Log T2 validado: 76 eventos, zero violações do schema.
- Reteste após prompt v4: T1 sucesso em 5 propostas; T2 sucesso em 7
  propostas, com uma repetição de ping rejeitada e registrada.
- T3 mock: sucesso com atualização, remoção e redistribuição.
- T4 mock: sucesso com ordem, feed, ping e confirmação.
- T4 Gemini real: sucesso em 20 propostas, com repetições redundantes.
- T3 Gemini real: incompleto em 20 propostas por repetição após a remoção;
  registrado como limitação da política, não como sucesso.
- Interface refinada: rótulos humanos, foco visível, status semântico,
  feedback acessível e cabeçalho responsivo; 70 testes aprovados.

Esses resultados verificam integração e robustez técnica; não são evidência de
usabilidade nem de alinhamento com participantes humanos.

## Próximas ações obrigatórias

1. Auditar os artefatos formais contra a interface concreta em um piloto técnico.
2. Confirmar parâmetros, recrutamento e revisão ética antes de qualquer coleta.
3. Manter T3/T4 independentes de qualquer ajuste em T1/T2.
4. Reabrir o congelamento somente com versão nova e hashes atualizados.

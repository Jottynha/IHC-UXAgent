# Caderno E1 — especificação formal complementar

Este caderno complementa `ihc_design_artifacts_v1.md` para a rubrica P3.
Modelos analíticos permanecem restritos ao analista e não são enviados ao LLM.

## CTT formal

Notação: `>>` sequência, `[>` desativação, `|>` suspensão para ajuda,
`|||` concorrência e `[]` escolha opcional.

```text
T1 =
  LerMissao >> LerCartoes >>
  (AtribuirFuncao)*3 >>
  Revisar >> Confirmar

T2 =
  LerPlano >> AtribuirPendente >>
  AtualizarFeed >>
  ((AtribuirPendente ||| Comunicar) [> Suporte) |>
  PedirAjuda >>
  Revisar >> Confirmar

T3 =
  LerPlano >> AtualizarFeed >>
  RemoverAtribuicao >>
  (AtribuirReserva ||| AtribuirTransporte) >>
  Revisar >> Confirmar

T4 =
  LerMissao >> AtualizarFeed >> DefinirOrdem >>
  (CompletarAtribuicoes ||| Comunicar) [>
  PedirAjuda >>
  Revisar >> Confirmar
```

`PedirAjuda` só ocorre quando `open_help` está em `available_actions`.
Uma rejeição não desativa a cena: retorna à mesma cena com feedback.

## MoLIC textual por falas

| Cena | Fala do usuário (`u:`) | Fala do preposto (`d:`) | Evento |
|---|---|---|---|
| S0 missão | `u: select_role` | `d: atribuição registrada` | `action_executed` |
| S1 parcial | `u: refresh_feed` | `d: observação atualizada` | `state_changed` |
| S1 parcial | `u: open_help(topic)` | `d: ajuda contextual aberta` | `support_opened` |
| S2 revisável | `u: review_plan` | `d: plano válido ou feedback` | `plan_submitted` |
| S3 revisado | `u: confirm_plan` | `d: tarefa concluída` | `task_evaluated` |
| T3 replanejamento | `u: remove_assignment` | `d: função liberada | `state_changed` |
| T4 integração | `u: set_step_order` | `d: ordem aceita ou rejeitada` | `state_changed` |
| Qualquer cena | `u: ação inválida` | `d: ruptura objetiva e recuperação` | `action_rejected` |

O verificador externo é uma transição paralela ao encerramento: ele consulta
o estado verdadeiro e não a fala do agente.

## Matriz de prevenção, ajuda e ruptura

| Operação | PP | PA | AL | RA | CE | MAC/log |
|---|---|---|---|---|---|---|
| Atribuir função | cartões e capacidades | ação incompatível ausente quando possível | checklist | feedback de capacidade | rejeição sem mutação | `CAPABILITY` |
| Atualizar feed | revisão visível | feed obsoleto bloqueia plano | botão de atualização | nova observação | rejeição por estado | `T2-FEED-UPDATE` |
| Comunicar | código exibido na tarefa | `send_ping` removido após uso | ajuda contextual | feedback de duplicidade | rejeição sem efeito | `T2-PING-ONCE` |
| Definir ordem | lista de etapas | ordem inválida rejeitada | ajuda de dependência | feedback da dependência | estado preservado | `STEP-COVERAGE` |
| Revisar | estado `reviewed` | confirmação indisponível antes da revisão | checklist | mensagem do controlador | rejeição prematura | `PLAN-VALID` |
| Confirmar | botão condicionado | plano incompleto rejeitado | ajuda/checklist | retorno à cena anterior | nenhum sucesso falso | `task_evaluated` |
| Remover atribuição | indisponibilidade visível | affordance só em T3 | ajuda de replanejamento | função vaga permanece visível | ação única | `TASK-AFFORDANCE` |

PP = prevenção passiva; PA = prevenção ativa; AL = prevenção apoiada;
RA = recuperação apoiada; CE = captura de erro. MAC é identificado por
assinaturas estruturadas, nunca por interpretação emocional do texto do LLM.

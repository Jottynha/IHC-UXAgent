# Tarefas de validação reservadas v2

**Status:** implementadas em código independente, mas reservadas para
validação; não usar resultados de T3/T4 para calibrar T1/T2.

**Data de congelamento:** 2026-11-05

**Configuração:** `uxagent-r1-r4-v2`; parâmetros permanecem hipóteses de
engenharia até comparação humana compatível.

## T3 — Replanejamento após indisponibilidade

- **Pré-condições:** quatro cartões; A atribuído a `LOCATE_RESOURCE`, C
  atribuído a `ACTIVATE_CHECKPOINT`, B e D disponíveis, sem transporte
  atribuído. Após a primeira observação, C fica indisponível.
- **Caminho:** atualizar o feed; executar `refresh_feed`; remover explicitamente
  a atribuição de C; atribuir ativação a D e transporte a B; revisar; confirmar.
- **Sucesso externo:** C não possui atribuição; as três funções aparecem uma vez;
  capacidades, disponibilidade e dependências são respeitadas; plano revisado e
  confirmado.
- **Cobertura:** R1 e R3.

## T4 — Integração de painéis

- **Pré-condições:** A atribuído a `LOCATE_RESOURCE`; B e C disponíveis para
  transporte e ativação; a ordem inicial é inválida; uma atualização de feed
  ocorre após a primeira proposta.
- **Caminho:** atualizar o feed; definir a ordem
  `LOCATE_RESOURCE → ACTIVATE_CHECKPOINT → TRANSPORT_RESOURCE`; enviar
  `NEXT_STEP_ACTIVATE_CHECKPOINT`; completar atribuições; revisar; confirmar.
- **Sucesso externo:** missão e feed integrados; dependências respeitadas;
  comunicação registrada; plano revisado e confirmado.
- **Cobertura:** R2, R3 e R4.

## Regra de independência

T3/T4 não entram em prompts, exemplos ou ajuste de parâmetros de T1/T2.
Qualquer alteração em tarefas, interface, prompt, mecanismos, avaliador ou
métricas após a abertura da validação exige novo conjunto reservado.

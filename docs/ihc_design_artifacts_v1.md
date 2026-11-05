# Artefatos formais de IHC — versão 1

Este documento formaliza os artefatos exigidos pela fase de Design UXAgent.
Ele refina as tarefas congeladas sem entregar HTA, CTT ou GOMS ao Gemini; o
agente recebe apenas signos observáveis e ações disponíveis.

## 1. Metamensagem

“Você está organizando uma equipe em um lobby cooperativo. A missão informa
três funções e suas dependências; os cartões mostram capacidades e
disponibilidade; o feed pode atualizar o estado da equipe. A interface oferece
atribuição, ordem, checklist, ajuda, atualização, comunicação, revisão e
confirmação. Você deve usar apenas o que está visível, corrigir conflitos,
revisar e confirmar um plano válido.”

O sistema comunica essa mensagem por:

- **signos estáticos:** objetivo, funções, dependências, cartões e ordem;
- **signos dinâmicos:** feed, revisão, status, feedback e disponibilidade das ações;
- **signos metalinguísticos:** checklist, ajuda contextual e mensagens de rejeição;
- **falas:** ações do vocabulário fechado em `uxagent_action.schema.json`.

O estado verdadeiro, identificadores internos, mecanismos R1--R4, gabarito e
critérios do avaliador não são signos entregues ao agente.

## 2. Mapa de objetivos e signos

| Objetivo | Signo visível | Fala possível | Registro |
|---|---|---|---|
| Entender a missão | painel Objetivo | `open_help` | `support_opened` |
| Escolher responsável | cartão + seletor de função | `select_role` | `action_executed` |
| Corrigir dependência | lista Ordem das etapas | `set_step_order` | `state_changed` |
| Atualizar conhecimento | revisão do Feed | `refresh_feed` | `state_changed` |
| Comunicar equipe | ação Ping disponível | `send_ping` | `action_executed` |
| Conferir plano | estado Revisado | `review_plan` | `action_executed` |
| Encerrar tarefa | botão Confirmar | `confirm_plan` | `task_evaluated` |
| Remover atribuição inválida | cartão indisponível em T3 | `remove_assignment` | `state_changed` |

Uma affordance ausente significa apenas que a fala não está disponível naquela
cena; a interface não expõe o motivo interno ou a probabilidade do mecanismo.

## 3. HTA refinada

### T1 — atribuição inicial

1. Organizar plano
   1.1 Ler objetivo e dependências  
   1.2 Consultar cartões  
   1.3 Atribuir as três funções  
   1.4 Revisar  
   1.5 Confirmar

### T2 — atualização e comunicação

1. Completar plano após atualização
   1.1 Ler plano parcial  
   1.2 Executar a primeira atribuição  
   1.3 Atualizar observação do feed  
   1.4 Completar atribuições restantes  
   1.5 Enviar `NEXT_STEP_ACTIVATE_CHECKPOINT`, se disponível  
   1.6 Revisar  
   1.7 Confirmar

### T3 — indisponibilidade

1. Replanejar após indisponibilidade
   1.1 Ler plano e cartões  
   1.2 Atualizar o feed  
   1.3 Remover a atribuição do integrante indisponível  
   1.4 Atribuir ativação ao integrante reserva  
   1.5 Atribuir transporte  
   1.6 Revisar  
   1.7 Confirmar

### T4 — integração de painéis

1. Integrar missão e feed
   1.1 Ler missão  
   1.2 Atualizar feed  
   1.3 Definir ordem válida  
   1.4 Completar atribuições  
   1.5 Enviar comunicação  
   1.6 Revisar  
   1.7 Confirmar

## 4. CTT textual

Notação: `>>` sequência, `[]` escolha opcional, `|||` concorrência
independente e `*` repetição.

```text
T1 = LerMissao >> LerCartoes >> (AtribuirFuncao)*3 >> Revisar >> Confirmar
T2 = LerPlano >> AtribuirPendente >> AtualizarFeed >>
     (AtribuirPendente ||| Comunicar) >> [Suporte] >> Revisar >> Confirmar
T3 = LerPlano >> AtualizarFeed >> RemoverAtribuicao >>
     (AtribuirReserva ||| AtribuirTransporte) >> Revisar >> Confirmar
T4 = LerMissao >> AtualizarFeed >> DefinirOrdem >>
     (CompletarAtribuicoes ||| Comunicar) >> [Suporte] >> Revisar >> Confirmar
```

Uma ação rejeitada retorna à cena atual; não avança a tarefa. Uma confirmação
sem revisão é uma ruptura e permanece na cena de plano.

## 5. GOMS/KLM de referência

Os operadores `M` (preparação mental), `P` (apontamento) e `K` (ativação) são
estimativas de método, não eventos nem segundos observados.

| Tarefa | Decomposição de referência | Ações observáveis |
|---|---|---:|
| T1 | `M M (P K)3 M P K M P K` | 5 |
| T2 | `(M P K)6` | 6 |
| T2 com suporte | `(M P K)6 + (M P K)` | 7 |
| T3 | `M M P K M (P K)2 M P K M P K` | 7 |
| T4 | `M M P K M P K (M P K)3 M P K M P K` | 8 |

As contagens T3/T4 são hipóteses de planejamento e devem ser auditadas contra
os controles finais. Não são convertidas em tempo humano nem usadas para
classificar erros.

## 6. MoLIC e rupturas

| Cena | Entrada | Fala | Próxima cena | Ruptura/recuperação |
|---|---|---|---|---|
| `S0 missão` | tarefa iniciada | `select_role` | `S1 plano parcial` | ação inválida permanece em `S0` |
| `S1 plano parcial` | atribuição aceita | `refresh_feed` | `S2 feed atualizado` | estado obsoleto exige atualização |
| `S2 feed atualizado` | feed visível | `send_ping`/atribuições | `S3 plano revisável` | ping duplicado é rejeitado |
| `S3 plano revisável` | funções cobertas | `review_plan` | `S4 revisado` | plano inválido retorna feedback |
| `S4 revisado` | plano válido | `confirm_plan` | `S5 concluído` | confirmação prematura permanece |
| `S1 T3` | integrante indisponível | `remove_assignment` | `S2 T3 replanejamento` | função vaga fica visível |
| `S1 T4` | painéis divergentes | `set_step_order` | `S2 T4 integração` | dependência inválida é rejeitada |

O controlador implementa essa máquina por pré-condições; o esquema de eventos
registra entrada, fala, ruptura e recuperação sem inferir intenção.

## 7. Ajuda e equivalência de canal

- Checklist: requisitos estáveis e ordem de conferência.
- Ajuda contextual: dependências, restrições de papel ou missão, quando a
  oportunidade está exposta.
- Feedback: consequência observável da última fala, sem revelar o estado
  verdadeiro oculto.
- O agente recebe o mesmo `view_model` que a interface renderiza; dados
  internos não usados pela persona são excluídos da observação.

## 8. Verificação antes de dados

1. Validar `view_model` e ações contra os schemas.
2. Verificar que T3/T4 não aparecem em prompts de T1/T2.
3. Executar cenários de sucesso, rejeição, suporte e atualização obsoleta.
4. Conferir que `synthetic=true` e que o avaliador externo usa o estado real.
5. Reabrir o congelamento se qualquer signo, prompt, schema ou regra mudar.

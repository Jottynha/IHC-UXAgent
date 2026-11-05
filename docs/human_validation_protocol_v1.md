# Protocolo de validação humana — versão-base

Este protocolo é um plano futuro; nenhuma coleta humana é realizada pelo
repositório atual.

## Status de prontidão

- Protocolo documentado: **sim**.
- Protótipo técnico e logs sintéticos: **sim**.
- Aprovação institucional: **pendente**.
- Consentimento, recrutamento e coleta: **bloqueados até aprovação**.
- T3/T4: reservadas para validação independente; não calibram T1/T2.

## Perfil e comparador

- Participantes adultos (18+), com familiaridade digital geral.
- **Perfil-alvo operacional:** adultos que jogam cooperativamente pelo menos
  semanalmente nos últimos três meses.
- **Comparador:** adultos com familiaridade digital geral e frequência de jogo
  em equipe de no máximo uma vez por mês nos últimos seis meses.
- Controlar dispositivo, instrução, ajuda e ordem das tarefas.
- Não usar o agente para diagnóstico ou para representar toda a população.

Os limiares de frequência são hipóteses operacionais e devem ser confirmados
antes do recrutamento.

## Tarefas e procedimento

1. Consentimento e triagem.
2. Instrução comum: “Organize as funções da equipe e confirme um plano que
   atenda aos requisitos da missão. Use os recursos disponíveis. A tarefa
   termina ao confirmar um plano ou atingir o limite.”
3. Executar T1--T4 com ordem contrabalanceada ou aleatorizada na validação
   formal.
4. Limite inicial: 30 ações executadas por tarefa.
5. Sessão incompleta com log íntegro conta como insucesso; perda técnica de log
   é reportada separadamente.
6. Registrar eventos equivalentes aos eventos sintéticos, com
   `synthetic=false` e identificador pseudonimizado.

T3/T4 permanecem independentes: seus resultados não podem ajustar mecanismos,
prompts, ajuda ou tarefas de calibração.

## Métricas prioritárias

- **Sucesso:** `S = N_ok / N_start`, por tarefa e condição.
- **Erros por oportunidade:** `E = n_err / n_opp`; denominador zero é
  indefinido, não zero.
- **Ações e sequência:** quantidade de ações executadas e
  `Dseq = Lev(a, a_ref) / max(n, n_ref, 1)`.
- **Uso de suporte:** métrica descritiva obrigatória.

Falhas técnicas são separadas de erros funcionais. Autorrelatos do LLM não são
medida humana; latência computacional não é tempo comportamental.

## Tolerâncias preliminares

As margens abaixo são hipóteses de engenharia a confirmar antes da abertura da
validação:

- `epsilon_S = 0,10`;
- `epsilon_E = 0,05 erro/oportunidade`;
- `epsilon_A = 1 ação/tarefa`.

O número de participantes não é fixado sem variabilidade piloto compatível.
Participantes são a unidade de reamostragem; tarefas da mesma pessoa não são
tratadas como observações independentes. Usar bootstrap por participante e
reportar intervalos para diferenças humanas, sintéticas e discrepância.

## Regra de decisão

Comparar perfil-alvo e comparador por tarefa:

`Delta_H = média_H,perfil - média_H,comparador`  
`Delta_S = média_S,perfil - média_S,comparador`  
`e = Delta_S - Delta_H`

Declarar alinhamento somente se a direção coincidir e o intervalo de incerteza
de `e` estiver inteiramente dentro da tolerância pré-fixada. Sem direção humana
determinável, o resultado é inconclusivo.

## Ética e proteção

O protótipo atual usa persona fictícia e dados sintéticos. Qualquer recrutamento,
piloto ou coleta deve ser submetido à avaliação institucional competente antes
do início, conforme o enquadramento aplicável. Registrar consentimento,
procedência/licença de dados secundários, risco de identificação, armazenamento,
retirada e contato responsável. Não coletar diagnóstico nem dados sensíveis
desnecessários.

## Critérios de congelamento

Antes de abrir T3/T4 ou recrutar participantes, registrar em conjunto:

- interface e signos;
- prompt e modelo;
- mecanismos e parâmetros;
- schemas e avaliador;
- tarefas reservadas;
- métricas, tolerâncias e análise;
- versão do protocolo e hash dos arquivos.

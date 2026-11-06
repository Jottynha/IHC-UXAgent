# UXAgent

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![JSON Schema](https://img.shields.io/badge/contratos-JSON%20Schema-0B7285)
![Gemini](https://img.shields.io/badge/LLM-Gemini-4285F4?logo=google&logoColor=white)
![Tests](https://img.shields.io/badge/testes-70%20aprovados-2E8B57)
![Status](https://img.shields.io/badge/status-prot%C3%B3tipo%20instrumentado-6F42C1)

> **Protótipo instrumentado de um UX-Agent para avaliação de interação em um
> lobby cooperativo.**

Este repositório implementa um **agente proxy**: um agente computacional que
substitui uma persona humana em tarefas controladas, executando ações em uma
interface e gerando dados sintéticos auditáveis. O sistema foi desenvolvido
para a fase de Desenvolvimento e Implementação do UX-Agent da disciplina de
Interação Humano-Computador (IHC).

O projeto **não representa jogadores humanos**, não diagnostica pessoas e não
permite concluir que o comportamento do Gemini seja comportamento humano. Os
resultados atuais são técnicos e sintéticos.

---

## Sumário

- [1. Contexto acadêmico](#1-contexto-acadêmico)
- [2. Conceitos fundamentais](#2-conceitos-fundamentais)
- [3. O que o professor solicitou](#3-o-que-o-professor-solicitou)
- [4. Solução implementada](#4-solução-implementada)
- [5. Tarefas T1--T4](#5-tarefas-t1t4)
- [6. Arquitetura](#6-arquitetura)
- [7. Segurança metodológica](#7-segurança-metodológica)
- [8. Estrutura do repositório](#8-estrutura-do-repositório)
- [9. Instalação](#9-instalação)
- [10. Como executar](#10-como-executar)
- [11. Testes e evidências](#11-testes-e-evidências)
- [12. Piloto e pacote E3](#12-piloto-e-pacote-e3)
- [13. Documentação de IHC](#13-documentação-de-ihc)
- [14. Estado atual e pendências](#14-estado-atual-e-pendências)
- [15. Limitações](#15-limitações)

---

## 1. Contexto acadêmico

O enunciado `UXAgent-P3.pdf` divide a entrega em duas frentes:

| Frente | Significado | Resultado esperado |
|---|---|---|
| **PI** | Projeto de Interação: especificar como a interface comunica, orienta e recupera erros | Metamensagem, signos, CTT, GOMS/KLM, MoLIC, ajuda e rupturas |
| **ISI** | Implementação do Sistema Instrumentado: transformar a especificação em software observável | Interface, agente LLM, mecanismos externos, logs, verificador e piloto |

O projeto também preserva a modelagem anterior: persona, tarefas, objetivos,
restrições e HTA. A implementação não substitui esses artefatos; ela os
operacionaliza em código, contratos e registros.

Documentos oficiais utilizados:

- [EnunciadoUXAgent.pdf](docs/EnunciadoUXAgent.pdf): requisitos gerais da disciplina.
- [UXAgent-P3.pdf](docs/UXAgent-P3.pdf): requisitos da fase de implementação.
- [HTSAgent-A2.pdf](docs/HTSAgent-A2.pdf): especificações de tarefas e agentes.
- [Modelagem__IHC_.pdf](docs/Modelagem__IHC_.pdf): modelagem de persona e tarefas.
- [UXAgentDesign-A3.pdf](docs/UXAgentDesign-A3.pdf): requisitos de design.

---

## 2. Conceitos fundamentais

### 2.1 IHC

**Interação Humano-Computador** estuda como pessoas e sistemas se comunicam,
incluindo interface, tarefas, feedback, erros, acessibilidade e avaliação.

### 2.2 UX-Agent

Um **UX-Agent** é um agente proxy baseado em LLM que usa uma aplicação no
lugar de uma persona. Ele recebe uma observação da interface, escolhe uma ação
permitida e tem sua execução registrada.

### 2.3 Persona

Uma **persona** é uma representação operacional de um perfil de usuário,
definida por objetivos, contexto, capacidades e restrições. Neste protótipo,
a persona é tratada como hipótese de modelagem; ela não é inferida a partir do
Gemini.

### 2.4 Estado verdadeiro

O **estado verdadeiro** é o estado interno completo do ambiente: atribuições,
disponibilidade, feed, ordem, revisão e critérios de sucesso. Ele pertence ao
ambiente e ao avaliador, não ao LLM.

### 2.5 Observação

Uma **observação** é a representação limitada da interface entregue ao agente.
Ela contém somente informações que a persona poderia perceber naquele momento.

### 2.6 Política

A **política** é o componente que escolhe a próxima ação. Pode ser:

- `MockPolicy`, usada para testes determinísticos;
- `GeminiActionPolicy`, usada para integrar o modelo Gemini.

A política propõe; ela não executa nem declara o sucesso da tarefa.

### 2.7 Controlador

O **controlador** verifica pré-condições, affordances, capacidades, dependências
e transições. Ele aceita ou rejeita cada proposta e registra a decisão.

### 2.8 Affordance

Uma **affordance** é uma possibilidade de ação percebida pelo usuário. No
UXAgent, `available_actions` informa quais falas estão disponíveis no estado
atual. Uma ação ausente não pode ser inventada pelo agente.

### 2.9 Instrumentação

**Instrumentação** é a inclusão de mecanismos para observar e registrar a
execução. Aqui, cada sessão gera eventos JSONL com timestamp, ator, tarefa,
observação, ação, rejeição, suporte, erro e resultado.

### 2.10 Verificador externo

O **verificador externo** calcula sucesso consultando o estado verdadeiro após
a execução. A afirmação do LLM nunca é aceita como prova de sucesso.

### 2.11 Dados sintéticos

**Dados sintéticos** são registros produzidos por políticas mock ou LLM, não por
participantes humanos. Eles servem para testar integração, rastreabilidade e
controlador, mas não comprovam usabilidade.

---

## 3. O que o professor solicitou

### 3.1 Parte I — Projeto de Interação

| Solicitação | Conceito | Situação |
|---|---|---|
| Metamensagem | Mensagem global que explica quem é o usuário, o que precisa fazer e como o sistema responde | Documentada |
| Paridade de signos | Correspondência entre signos vistos na tela e signos enviados ao agente | Documentada; deve continuar sendo auditada a cada mudança |
| CTT | `ConcurTaskTrees`: notação para representar temporalidade, concorrência, desativação e ajuda | Formalizada no caderno E1 |
| GOMS/KLM | Modelo de objetivos e operadores; KLM estima a sequência de ações de um especialista | Linha de base documentada; comparação técnica produzida |
| MoLIC | Modelo da interação como diálogo entre usuário e preposto do sistema | Modelo textual com falas `u:` e `d:` documentado |
| MAC e rupturas | Identificação objetiva de falhas de comunicação por assinaturas observáveis | Matriz PP/PA/AL/RA/CE documentada |
| Ajuda sob demanda | Ajuda apresentada após uma ação explícita de solicitação | `open_help`, checklist e feedback implementados |

### 3.2 Parte II — Implementação do Sistema Instrumentado

| Solicitação | Implementação |
|---|---|
| Aplicação interativa | Interface web local em `uxagent_web.py` |
| Registro JSON estruturado | `event_logger.py` e `uxagent_event.schema.json` |
| Mecanismos fora do prompt | R1--R4 em `mechanisms.py` e `controller.py` |
| Agente proxy LLM | `gemini_client.py` |
| Tradutor de observação | `UXAgentSession` e `observation_snapshot()` |
| Ações restritas por estado | `available_actions`, schema e pré-condições |
| Verificador externo | `externally_evaluate()` nos ambientes |
| Piloto técnico | `pilot_e3/` e `pilot_e3.zip` |
| Repositório executável | README, dependências, configurações, modo mock e testes |

---

## 4. Solução implementada

O fluxo de uma ação é:

```text
Estado verdadeiro
      |
      v
Observação limitada da interface
      |
      v
Política mock ou Gemini
      |
      v
Ação estruturada validada pelo schema
      |
      v
Controlador: pré-condições, mecanismos e transição
      |
      +--> ação aceita --> novo estado + evento
      |
      +--> ação rejeitada --> feedback + evento de ruptura
      |
      v
Verificador externo
```

O agente não acessa diretamente:

- estado verdadeiro completo;
- gabarito;
- HTA;
- CTT;
- GOMS/KLM;
- regras internas do avaliador;
- parâmetros ocultos dos mecanismos.

---

## 5. Tarefas T1--T4

### T1 — Atribuição inicial

O agente deve atribuir as três funções complementares a integrantes capazes,
revisar o plano e confirmar.

### T2 — Atualização e comunicação

Além da atribuição, exige atualização explícita do feed e comunicação da
próxima etapa quando `send_ping` estiver disponível.

### T3 — Replanejamento

Uma atribuição torna-se inválida. O agente deve atualizar o feed, remover a
atribuição de `member_C`, redistribuir a função para `member_D`, atribuir
transporte a `member_B`, revisar e confirmar.

### T4 — Integração de painéis

O agente deve atualizar o feed, definir a ordem correta, comunicar a próxima
etapa, completar as atribuições, revisar e confirmar.

### Separação metodológica

T1/T2 são tarefas de **calibração**. Calibração significa testar se o
controlador, os mecanismos e a instrumentação se comportam como esperado.

T3/T4 são tarefas de **validação reservada**. Seus resultados não podem ser
usados para ajustar prompt, mecanismos, ajuda ou interface de T1/T2.

---

## 6. Arquitetura

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Ambiente | `environment.py` | Estado verdadeiro, regras e avaliadores de T1--T4 |
| Controlador | `controller.py` | Pré-condições, transições, rejeições e R1--R4 |
| Política | `uxagent_cli.py`, `gemini_client.py` | Mock determinístico ou proposta Gemini |
| Fachada | `uxagent_session.py` | Contrato usado pela interface |
| Vocabulário | `uxagent_actions.py` | Ações, templates e versões de contrato |
| Interface | `uxagent_web.py` | Lobby web local |
| Instrumentação | `event_logger.py` | Eventos JSONL validados |
| Métricas | `metrics.py`, `tools/analyze_pilot.py` | Resumos e métricas do piloto |
| Contratos | `*.schema.json` | Validação de ações, eventos e interface |

### Contratos versionados

- Interface: `ui-contract-v2`.
- Prompt: `uxagent-action-prompt-v4`.
- Eventos: schema `1.0`.
- Mecanismos: `uxagent-r1-r4-v2`.

---

## 7. Segurança metodológica

### R1--R4

Os mecanismos comportamentais são parâmetros controlados fora do prompt:

- **R1 — validação/erro:** oportunidade de erro operacional.
- **R2 — comunicação:** oportunidade de enviar uma comunicação.
- **R3 — estado fresco:** oportunidade de exigir atualização da observação.
- **R4 — ajuda exposta:** oportunidade de disponibilizar ajuda contextual.

Eles são desligados por padrão e podem ser ativados por configuração.

### Fronteira de informação

A fronteira de informação impede que o agente receba dados do analista. A
interface humana e a observação do LLM devem manter paridade de signos, sem
vazar gabarito ou critérios ocultos.

### Rejeições

Uma ação inválida não altera silenciosamente o estado. O controlador registra:

1. ação proposta;
2. motivo da rejeição;
3. categoria do erro;
4. oportunidade associada;
5. feedback observável.

---

## 8. Estrutura do repositório

```text
.
├── controller.py
├── environment.py
├── event_logger.py
├── gemini_client.py
├── mechanisms.py
├── metrics.py
├── uxagent_actions.py
├── uxagent_cli.py
├── uxagent_session.py
├── uxagent_web.py
├── *.schema.json
├── tests/
├── tools/
├── pilot_e3/
├── pilot_e3.zip
└── docs/
```

Documentação central:

- [requirements_traceability.md](docs/requirements_traceability.md): requisito,
  implementação e evidência.
- [ihc_design_artifacts_v1.md](docs/ihc_design_artifacts_v1.md): metamensagem,
  signos, HTA, CTT, GOMS/KLM e MoLIC.
- [design_specification_e1.md](docs/design_specification_e1.md): CTT, falas
  MoLIC e matriz MAC complementar.
- [human_validation_protocol_v1.md](docs/human_validation_protocol_v1.md):
  protocolo, métricas, tolerâncias e ética.
- [repository_review_2026-11-05.md](docs/repository_review_2026-11-05.md):
  revisão contra os documentos oficiais.
- [freeze_manifest_v6.json](docs/freeze_manifest_v6.json): congelamento técnico.

---

## 9. Instalação

No PowerShell, na raiz do repositório:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se o Python 3.14 não estiver disponível, use uma versão compatível instalada
e mantenha o ambiente virtual isolado:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 10. Como executar

### 10.1 Modo mock

O modo mock não usa API nem gera custo. Ele é o primeiro teste recomendado:

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T1
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T2
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T3
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T4
```

Resultado esperado:

```text
RESULTADO: SUCESSO
```

### 10.2 Interface web

```powershell
.\.venv\Scripts\python.exe uxagent_web.py --task T1
```

Abra <http://127.0.0.1:8765/>.

Para testar outra tarefa, encerre o servidor e execute `--task T2`, `--task
T3` ou `--task T4`.

### 10.3 Mecanismos

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py `
  --mock --task T2 --enable R2,R3,R4 --seed 42
```

Configuração diagnóstica:

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py `
  --mock --task T2 `
  --enable R2,R3,R4 `
  --config config_diagnostica_R2_R3_R4.json `
  --seed 42
```

### 10.4 Gemini

Crie o arquivo local de ambiente:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `GEMINI_API_KEY` e execute:

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py --task T1 --max-steps 20
.\.venv\Scripts\python.exe uxagent_cli.py --task T2 --max-steps 30
```

O `.env` é ignorado pelo Git. Nunca inclua a chave em código, logs, traces ou
commits.

### 10.5 Traces de prompt e contexto

Para o pacote E3, o rastreamento é opcional e explícito:

```powershell
$env:UXAGENT_TRACE_DIR = "$PWD\gemini_traces"
.\.venv\Scripts\python.exe uxagent_cli.py --task T1 --max-steps 20
Remove-Item Env:\UXAGENT_TRACE_DIR
```

Os arquivos registram o contexto e o prompt enviados, mas não registram a
chave de API.

---

## 11. Testes e evidências

Execute a suíte completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado congelado:

```text
70 passed
```

Outras verificações:

```powershell
.\.venv\Scripts\python.exe -m py_compile `
  gemini_client.py tools/run_pilot.py tools/analyze_pilot.py
git diff --check
```

Os logs são artefatos de execução e ficam em `logs/` quando essa pasta é
explicitamente usada. Ela é ignorada pelo Git e não é fonte de requisitos.

---

## 12. Piloto e pacote E3

O piloto técnico reproduzível está em [pilot_e3/](pilot_e3) e pode ser
regenerado com:

```powershell
.\.venv\Scripts\python.exe tools/run_pilot.py --seeds 42,43,44
.\.venv\Scripts\python.exe tools/analyze_pilot.py
```

O pacote compactado está em [pilot_e3.zip](pilot_e3.zip).

Conteúdo:

- seis sessões mock: T1/T2 com três sementes;
- logs JSONL;
- dicionário de campos;
- manifest do piloto;
- métricas `S`, `R`, `E`, `A` e uso de ajuda;
- comparação de contagem de ações com KLM;
- uma execução real Gemini de T1;
- uma execução real Gemini de T2;
- traces de prompts e contextos efetivamente enviados.

### Significado das métricas

| Métrica | Definição |
|---|---|
| `S` | Sucesso calculado externamente por sessão |
| `R` | Recuperação bem-sucedida após erro; nulo quando não houve oportunidade |
| `E` | Quantidade de eventos de erro funcional |
| `A` | Quantidade de ações executadas |
| Ajuda | Quantidade de eventos `support_opened` |

O KLM fornece uma referência de sequência de ações de especialista. Ele não é
um cronômetro humano neste protótipo e não deve ser interpretado como medida
de tempo real sem calibração experimental.

---

## 13. Documentação de IHC

| Documento | Conteúdo |
|---|---|
| [ihc_design_artifacts_v1.md](docs/ihc_design_artifacts_v1.md) | Metamensagem, signos, HTA, CTT, GOMS/KLM e MoLIC |
| [design_specification_e1.md](docs/design_specification_e1.md) | CTT formal, falas `u:`/`d:` e matriz PP/PA/AL/RA/CE |
| [human_validation_protocol_v1.md](docs/human_validation_protocol_v1.md) | Perfil, procedimento, métricas, tolerâncias e ética |
| [e3_field_dictionary.md](docs/e3_field_dictionary.md) | Dicionário dos eventos e traces |
| [demo_script_3_to_5_min.md](docs/demo_script_3_to_5_min.md) | Roteiro da demonstração |
| [institutional_review_checklist.md](docs/institutional_review_checklist.md) | Preparação para revisão institucional |
| [requirements_traceability.md](docs/requirements_traceability.md) | Matriz requisito--implementação--evidência |
| [freeze_manifest_v6.json](docs/freeze_manifest_v6.json) | Hashes e escopo congelado |

### Demonstração

O roteiro de 3--5 minutos está em
[demo_script_3_to_5_min.md](docs/demo_script_3_to_5_min.md). O roteiro está
pronto, mas o vídeo precisa ser gravado pelo grupo; o repositório não afirma
que um arquivo de vídeo já exista.

### Relatório IEEE

O enunciado solicita um artigo IEEE de até oito páginas, acompanhado do
caderno de design. A fonte `.tex` deve ser compilada em uma instalação LaTeX
com `IEEEtran`. O repositório mantém a documentação e as evidências técnicas;
o PDF final depende dessa compilação e da revisão autoral do grupo.

---

## 14. Estado atual e pendências

### Implementado

- T1--T4 e seus ambientes independentes.
- Interface web local refinada.
- Integração opcional com Gemini.
- Modo mock determinístico.
- Schemas de ações, eventos e interface.
- R1--R4 parametrizados fora do prompt.
- Avaliação externa pelo estado verdadeiro.
- Logs JSONL auditáveis.
- Testes automatizados.
- Piloto técnico e pacote E3.
- Caderno E1 e protocolo humano.
- Congelamento técnico v6.

### Pendente

- Compilar e revisar o PDF IEEE final.
- Gravar a demonstração de 3--5 minutos.
- Submeter o protocolo à instância institucional competente.
- Obter aprovação antes de qualquer recrutamento.
- Executar validação humana somente após consentimento e autorização.
- Não usar T3/T4 para calibrar T1/T2.

---

## 15. Limitações

- R1--R4 são hipóteses de engenharia, não probabilidades humanas.
- O modo mock testa integração e oráculos, não qualidade do modelo.
- O Gemini pode repetir ações; o controlador rejeita e registra essas tentativas.
- T2 real pode atingir o limite de passos sem sucesso.
- A interface ainda é um protótipo de baixa fidelidade visual.
- O pacote E3 atual é técnico e sintético.
- Não há aprovação institucional registrada.
- Nenhum resultado atual permite inferir usabilidade, perfil humano ou validade
  ecológica.

## Estado de congelamento

O estado documentado neste README corresponde ao
[freeze_manifest_v7.json](docs/freeze_manifest_v7.json). Alterações em código,
interface, prompt, schemas, mecanismos, modelo, avaliador ou protocolo exigem
nova revisão e novo manifesto.

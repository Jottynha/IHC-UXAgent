# UXAgent

Protótipo sintético para depurar um protocolo de avaliação de interação em um
lobby cooperativo. O projeto separa ambiente, observação, política, controlador,
instrumentação e avaliador externo. Ele **não representa jogadores humanos** e
não deve ser usado para inferir comportamento real.

## Estado atual

- T1 e T2 implementadas e executáveis.
- R1--R4 parametrizados, desligados por padrão e fora do prompt do modelo.
- Ações fechadas e validadas por JSON Schema.
- Avaliador externo baseado no estado verdadeiro.
- Logs JSONL validados pelo schema de eventos.
- Fachada `UXAgentSession` pronta para uma futura interface web/desktop.
- T3 e T4 implementadas em versão independente para validação reservada.
- Interface web local de baixa fidelidade implementada; design visual final ainda não implementado.
- Base técnica congelada para reprodução em [`docs/freeze_manifest_v2.json`](docs/freeze_manifest_v2.json).

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| `environment.py` | Estado verdadeiro, regras e oráculos de T1/T2 |
| `controller.py` | Pré-condições, transições e mecanismos R1--R4 |
| `uxagent_session.py` | Fachada para interface e integração, sem expor estado indevido |
| `uxagent_actions.py` | Vocabulário, templates e validação de ações |
| `gemini_client.py` | Adaptador opcional para Gemini |
| `event_logger.py` | Eventos JSONL validados |
| `metrics.py` | Resumos auditáveis de sessões |
| `resumir_logs_uxagent.py` | Resumo seguro de logs |
| `uxagent_cli.py` | Executor CLI de T1/T2 |
| `uxagent_action.schema.json` | Contrato de ações |
| `uxagent_event.schema.json` | Contrato de eventos |
| `uxagent_ui.schema.json` | Contrato do modelo entregue à interface |
| `uxagent_mechanisms.json` | Configuração padrão de mecanismos |
| `config_diagnostica_R2_R3_R4.json` | Configuração extrema para testes determinísticos |
| `tests/` | Testes de schemas, domínio, mecanismos, CLI e fachada |
| `docs/` | Requisitos, modelagem, design e rastreabilidade |

## Instalação

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Execução sem API

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T1
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T2
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T3
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T4
.\.venv\Scripts\python.exe uxagent_web.py --task T1
```

Abra `http://127.0.0.1:8765/` para usar o lobby local. A interface chama
`UXAgentSession`, mantém T1/T2 no mesmo controlador da CLI, exibe apenas as
ações permitidas e oferece avaliação externa após a confirmação. O servidor web
grava os eventos em `logs/` quando iniciado pelo comando acima.

Ativando mecanismos:

```powershell
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T2 --enable R2,R3,R4 --seed 42
.\.venv\Scripts\python.exe uxagent_cli.py --mock --task T2 --enable R2,R3,R4 `
  --config config_diagnostica_R2_R3_R4.json --seed 42
```

Cada execução cria `logs/<session-id>.jsonl`. A pasta é resultado de execução e
não deve conter dados reais nem ser usada como fonte de requisitos.

## Execução com Gemini

Copie `.env.example` para `.env`, abra o arquivo e substitua
`cole_sua_chave_aqui` pela sua chave do Gemini. O `.env` está no `.gitignore` e
não deve ser commitado:

```powershell
Copy-Item .env.example .env
notepad .env
.\.venv\Scripts\python.exe uxagent_cli.py --task T2 --max-steps 20
```

Também é possível definir `GEMINI_API_KEY` ou `GOOGLE_API_KEY` diretamente no
ambiente do terminal; variáveis já exportadas têm prioridade sobre `.env`.
Nunca compartilhe a chave nem a registre em logs.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q .
```

## Decisão sobre implementar a interface

**Sim, já podemos iniciar a interface de baixa fidelidade e a implementação
visual de T1/T2**, porque os requisitos essenciais estão definidos:

1. tarefas, objetivos e critérios de sucesso externos;
2. vocabulário de ações e pré-condições;
3. separação entre estado verdadeiro e observação;
4. suporte por checklist, ajuda, feed e ping;
5. eventos e métricas mínimas;
6. mecanismos controláveis e configuração versionada;
7. testes automatizados para o núcleo.

O mesmo `UXAgentSession`,
`view_model()` e `dispatch()` deve ser usado pela GUI e pelos testes.

O congelamento técnico foi realizado, mas ele não representa aprovação para
validação humana. A revisão detalhada contra os PDFs oficiais está em
[`docs/repository_review_2026-11-05.md`](docs/repository_review_2026-11-05.md).
Ainda faltam os artefatos formais de HTA, CTT, GOMS/KLM, MoLIC, metamensagem,
signos, protocolo humano, tolerâncias e aprovação ética.

O contrato visual está versionado como `ui-contract-v2`; o prompt estruturado
está versionado como `uxagent-action-prompt-v4`. Uma interface deve rejeitar
ou adaptar explicitamente versões incompatíveis, nunca interpretar campos por
posição ou por texto livre.

## Limitações

Os números de R1--R4 são hipóteses de engenharia, não probabilidades humanas.
O modo mock testa integração e oráculos, não qualidade do modelo. Logs sintéticos
não substituem participantes, métricas humanas ou validação externa.

Os PDFs de requisitos estão em [`docs/`](docs/). T3/T4 estão descritas em
[`Tarefas_validacao_reservadas_v1.md`](Tarefas_validacao_reservadas_v1.md) e
implementadas sem usar seus resultados para calibrar T1/T2.
A matriz de rastreabilidade está em
[`docs/requirements_traceability.md`](docs/requirements_traceability.md).
Os artefatos HTA, CTT, GOMS/KLM e MoLIC estão em
[`docs/ihc_design_artifacts_v1.md`](docs/ihc_design_artifacts_v1.md). O plano
humano está em
[`docs/human_validation_protocol_v1.md`](docs/human_validation_protocol_v1.md).

# Roteiro da demonstração funcional (3–5 minutos)

Este roteiro permite uma apresentação ao vivo ou gravação posterior. Nenhum
vídeo é afirmado como existente no repositório.

## 0:00–0:30 — Contexto

Apresentar a pergunta do projeto: o agente recebe somente a observação que a
persona teria. Mostrar que T1/T2 são calibração e que T3/T4 permanecem
reservadas.

## 0:30–1:20 — Interface e observação

Executar:

```powershell
py -3 uxagent_web.py --task T1
```

Abrir `http://127.0.0.1:8765/`. Mostrar objetivo, cartões, ações disponíveis,
feedback, revisão e histórico. Destacar que a interface não mostra o estado
verdadeiro nem o gabarito do avaliador.

## 1:20–2:20 — Execução mock auditável

Em outro terminal:

```powershell
$env:UXAGENT_LOG_DIR = "$PWD\demo_logs"
py -3 uxagent_cli.py --mock --task T1 --max-steps 20
Remove-Item Env:\UXAGENT_LOG_DIR
```

Mostrar `RESULTADO: SUCESSO`, a quantidade de ações e uma linha de
`demo_logs/*.jsonl`. Explicar que o sucesso vem do avaliador externo.

## 2:20–3:20 — Gemini e rejeição controlada

Com `.env` configurado:

```powershell
$env:UXAGENT_LOG_DIR = "$PWD\demo_logs"
$env:UXAGENT_TRACE_DIR = "$PWD\demo_traces"
py -3 uxagent_cli.py --task T2 --max-steps 30
Remove-Item Env:\UXAGENT_LOG_DIR
Remove-Item Env:\UXAGENT_TRACE_DIR
```

Mostrar no terminal uma ação aceita e, se ocorrer, uma repetição de
`send_ping` rejeitada. Abrir um trace JSON e mostrar que ele contém contexto e
prompt, mas nenhuma chave.

## 3:20–4:20 — Verificação e rastreabilidade

Mostrar:

- `pilot_e3/metrics.json`;
- `uxagent_event.schema.json`;
- `docs/ihc_design_artifacts_v1.md`;
- `docs/freeze_manifest_v4.json`.

Explicar a diferença entre log sintético, hipótese KLM e evidência humana.

## 4:20–5:00 — Limitações

Informar que T3/T4 não calibram T1/T2, que a validação humana depende de
aprovação institucional e que o vídeo final ainda precisa ser gravado pelo
grupo.

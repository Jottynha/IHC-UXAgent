# Ferramentas de reprodução

## Piloto E3

Na raiz do repositório:

```powershell
py -3 tools/run_pilot.py --seeds 42,43,44
```

O comando cria `pilot_e3/` com logs JSONL, saídas de terminal e
`pilot_manifest.json`. A política mock não envia prompt a um LLM; por isso
essa execução é usada para testar o controlador e a instrumentação.

## Rastreamento Gemini

Para registrar prompt e contexto efetivamente enviados sem registrar a chave:

```powershell
$env:UXAGENT_TRACE_DIR = "$PWD\pilot_e3\gemini_traces"
py -3 uxagent_cli.py --task T1 --max-steps 20
Remove-Item Env:\UXAGENT_TRACE_DIR
```

Cada arquivo de trace contém modelo, versão do prompt, contexto JSON e prompt
enviado. Nunca inclua `.env` nem chaves no pacote.

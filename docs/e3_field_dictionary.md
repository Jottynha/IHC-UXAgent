# Dicionário de campos E3

## Eventos JSONL

| Campo | Significado |
|---|---|
| `schema_version` | Versão do contrato de eventos |
| `sid` | Identificador da sessão |
| `tid` | Tarefa sintética |
| `cond` | Condição experimental |
| `actor` | Autor do evento |
| `synthetic` | Origem sintética do registro |
| `cfg_ver` | Versão da configuração |
| `ui_ver` | Versão do contrato de interface |
| `llm_model` | Modelo usado, quando aplicável |
| `prompt_ver` | Versão do prompt, quando aplicável |
| `step` | Passo da sessão |
| `event` | Tipo do evento |
| `ts_sys` | Timestamp UTC |
| `obs_id` | Identificador da observação |
| `state_pre` / `state_post` | Estado antes/depois, conforme o contrato |
| `act_prop` / `act_exec` | Ação proposta/executada |
| `reject` | Motivo de rejeição |
| `support` | Ajuda aberta |
| `error` | Erro funcional e oportunidade |
| `opp_id` | Identificador da oportunidade |
| `outcome` | Resultado do avaliador externo |
| `tech_fail` | Falha técnica |

## Traces Gemini

`context` é a observação entregue ao modelo; `prompt` é o texto completo
enviado, sem credenciais. `sequence`, `timestamp`, `model` e
`prompt_version` permitem reprodutibilidade e auditoria.

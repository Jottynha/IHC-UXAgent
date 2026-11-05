# Pacote E3 — piloto técnico

Este pacote contém evidência técnica sintética e uma amostra real do Gemini
para as tarefas de calibração T1/T2.

- `t*-seed-*`: seis sessões mock reproduzíveis, três sementes por tarefa.
- `metrics.json` e `metrics.md`: métricas `S`, `R`, `E`, `A`, ajuda e diferença
  de ações em relação à referência KLM.
- `gemini_real/logs/`: uma execução real de T1 e uma de T2.
- `gemini_real/traces/`: prompt e contexto efetivamente enviados, sem chave.
- `gemini_real_results.json`: resumo da amostra real.
- `field_dictionary.md`: dicionário dos eventos e traces.
- `pilot_manifest.json`: configuração e procedência do piloto mock.

O mock teve sucesso em todas as seis sessões. A execução real do Gemini teve
sucesso em T1 e atingiu o limite de passos em T2. Isso é limitação observada,
não sucesso artificial.

Os dados são sintéticos e não constituem validação humana.

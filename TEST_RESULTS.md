# Resultado de verificação — R1–R4

Data da revisão: 2026-10-17 (revisão v2 após análise dos logs Gemini).

## Testes automatizados

Comando executado:

```bash
python -m unittest discover -s tests -v
```

**Resultado: 54 testes aprovados.** `python -m compileall -q .` também concluiu sem erro.

A suíte cobre os schemas de ações e eventos; operações do controlador; probabilidade-limite de cada mecanismo (0 e 1); T1 e T2 com política mock; injeção R1 registrada como diferença entre ação proposta e executada; falha esperada quando R2 remove a oportunidade obrigatória de ping; e recuperação de feed obsoleto de R3 com `refresh_feed`.

## Verificações ponta a ponta

- T1 sem mecanismos: sucesso no modo mock.
- T2 sem mecanismos: sucesso no modo mock.
- R1 forçado em `p_valida=0`: o controlador registra o deslize e a T1 com um passo termina incompleta, como esperado para o teste de injeção.
- R2 forçado em `p_comunicar=0`: o ping é ocultado e a T2 termina em falha externa, porque a tarefa requer comunicar a próxima etapa.
- R3 forçado em `p_estado_fresco=0`: a primeira observação fica obsoleta; a política mock usa `refresh_feed` e conclui a T2.
- R4 forçado em `p_ajuda_exposta=0`: `open_help` fica oculto, mas o checklist continua disponível; T2 pode ser concluída sem usar ajuda contextual.
- R2/R3/R4 combinados em uma semente de demonstração: T2 concluída no modo mock quando a oportunidade de ping está disponível e o estado fresco é exposto.
- Revisão v2: após os logs reais mostrarem cinco pings repetidos em T2, o controlador passou a ocultar `send_ping` após o ping correto e rejeitar duplicatas/códigos incorretos. Os novos testes unitários cobrem esses três comportamentos. T2 mock, com R2/R3/R4 ativados, concluiu em 5 ações e registrou exatamente um ping.

Os registros gerados foram validados contra `uxagent_event.schema.json`.

## Limite da validação

Esses resultados verificam a lógica do controlador e do avaliador em cenários sintéticos. **Não são resultados de novas chamadas à Gemini API, não validam o comportamento como representante de pessoas e não incluem participantes humanos.** A integração real com Gemini deve ser executada novamente no computador do grupo usando a chave já guardada localmente, agora com a configuração v2. Ainda não foi feita uma nova chamada real após esta correção.

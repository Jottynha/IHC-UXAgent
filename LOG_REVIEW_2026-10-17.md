# Revisão dos logs do UXAgent — 17/10/2026

## Resumo das quatro sessões enviadas

- As duas sessões sem modelo registrado parecem ser execuções `--mock`; servem como verificação de integração, não como evidência sobre o Gemini.
- T1 com Gemini, R1 ligado: terminou em sucesso, registrou dois deslizes de R1 e nenhuma falha técnica. Isso mostra recuperação neste cenário, não valida a probabilidade de R1 como estimativa humana.
- T2 com Gemini, R2/R3/R4 ligados: terminou em sucesso e não teve falha técnica, mas registrou 10 ações, incluindo cinco pings iguais. R2 deixava a ação visível depois de enviar a comunicação exigida.
- Na sessão T2, R3 não produziu observação obsoleta (`0/10`); a amostragem de estado fresco pode explicar isso. Para verificar o ramo desatualizado, usar teste determinístico com `p_estado_fresco=0.0`.
- R4 ficou oculto em todas as observações. Como `p_ajuda_exposta=0.25` é sorteado uma vez por oportunidade/sessão no protótipo, isso pode ocorrer; para verificar exposição, usar teste determinístico com `p_ajuda_exposta=1.0`.

## Correção feita nesta versão v2

O controlador agora remove `send_ping` das ações visíveis após registrar o código exigido `NEXT_STEP_ACTIVATE_CHECKPOINT`; envio repetido e código incorreto são rejeitados e registrados. A versão da configuração foi elevada para `uxagent-r1-r4-v2` para distinguir logs novos dos antigos.

## Verificação após a correção

- 54 testes automatizados passaram.
- T2 com política mock e R2/R3/R4 ligados concluiu com sucesso em 5 ações e exatamente um ping executado.
- Os testes determinísticos de R3 (estado obsoleto/refresh) e R4 (ajuda exposta/oculta) continuam passando.
- Ainda é necessário repetir T2 com Gemini real para verificar o comportamento da política após a correção. Nenhuma chave da API foi incluída neste arquivo.

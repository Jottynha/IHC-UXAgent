# UXAgent — protótipo T1/T2 com Gemini e mecanismos R1–R4

Este pacote implementa duas tarefas de calibração sintéticas, sem interface gráfica. O Gemini propõe uma ação estruturada; o controlador local executa as regras e mecanismos; o avaliador externo calcula o resultado pelo estado verdadeiro do ambiente; e os eventos são gravados em JSONL validado pelo schema do projeto.

**Importante:** R1–R4 são hipóteses de engenharia para depurar o protótipo. Não representam probabilidades medidas de jogadores humanos e não validam que o agente imita pessoas. T3/T4 permanecem reservadas e não são executadas neste pacote.

## Mecanismos implementados

- **R1 — `p_valida = 0.90`:** nas oportunidades válidas de `select_role`, o controlador mantém a proposta com a probabilidade configurada. Caso contrário, injeta um deslize de atribuição usando uma ação permitida pelo schema, mas incompatível com a capacidade declarada do integrante. O deslize modifica o estado, fica registrado como erro `operational_slip`, com regra identificada como R1 e deve ser detectado/corrigido pela política ou pelo avaliador.
- **R2 — `p_comunicar = 0.65`:** em T2, depois do evento de atualização do feed, define se a ação `send_ping` fica exposta. Se não há oportunidade, a ação não aparece no menu visível e uma tentativa direta é rejeitada. Quando o ping correto `NEXT_STEP_ACTIVATE_CHECKPOINT` é enviado, `send_ping` sai do menu de ações e um envio repetido é rejeitado; T2 exige comunicar a próxima etapa uma vez, não repetir mensagens.
- **R3 — `p_estado_fresco = 0.70`:** em T2, quando chega a atualização predefinida, o controlador decide uma vez se a informação nova será entregue à observação. Se falhar, o agente continua vendo o cache antigo até chamar `refresh_feed`. O estado verdadeiro permanece separado para o avaliador e para os logs.
- **R4 — `p_ajuda_exposta = 0.25`:** controla a exposição da ação `open_help` na oportunidade de incerteza. Não representa a probabilidade de uma pessoa procurar ajuda. O checklist permanece como recurso separado.

Todas as chaves vêm desligadas por padrão. Os valores/probabilidades são carregados de `uxagent_mechanisms.json`; a configuração efetiva e uma impressão digital curta aparecem no log para reprodutibilidade.

## Instalação (Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Testar sem API e sem custo

T1, linha de base:

```bash
python run_uxagent_t1.py --mock --task T1
```

T2, linha de base:

```bash
python run_uxagent_t1.py --mock --task T2
```

Executar a suíte completa:

```bash
python3 -m unittest discover -s tests -v
```

O cálculo auditável das métricas mínimas está em `metrics.py`:

```python
from metrics import summarize_session, summarize_sessions
```

`summary["success"]` é `None` quando a sessão não permite avaliação independente, por exemplo após falha técnica. Denominadores nulos também retornam `None`; resultados sintéticos não são convertidos em medidas humanas.

Resumir logs sem despejar estados e notas brutas (copie o resumo para compartilhar, nunca a chave API):

```bash
python resumir_logs_uxagent.py --all --output resumo_logs_uxagent.txt
```

## Executar com Gemini

Use somente a chave nova criada após revogar a chave exposta. Não a salve em arquivos, não a inclua no código e não a envie por mensagem. Use apenas estados fictícios.

```bash
read -rsp "Chave Gemini API: " GEMINI_API_KEY
echo
export GEMINI_API_KEY
python run_uxagent_t1.py --task T1 --max-steps 20
```

Para testar T2, use `--task T2`. Cada ação proposta pelo Gemini pode consumir uma chamada da API.

## Ativar mecanismos

Ativar só R1 na tarefa T1 (a semente 2 demonstra a injeção de pelo menos um deslize com a sequência aleatória atual):

```bash
python run_uxagent_t1.py --mock --task T1 --enable R1 --seed 2
```

R2 e R3 têm oportunidades definidas em T2; se ativados em T1, o programa avisa que não alteram essa tarefa.

Ativar R2, R3 e R4 em T2:

```bash
python run_uxagent_t1.py --mock --task T2 --enable R2,R3,R4 --seed 42
```

Para uma verificação diagnóstica dos caminhos raros, existe `config_diagnostica_R2_R3_R4.json`: R2=1.0 sempre expõe o ping, R3=0.0 força uma observação obsoleta até `refresh_feed`, e R4=1.0 expõe a ajuda contextual. É uma configuração extrema apenas para verificar o código, não para calibrar ou representar jogadores:

```bash
python run_uxagent_t1.py --mock --task T2 --enable R2,R3,R4 --config config_diagnostica_R2_R3_R4.json --seed 42
```

Ativar todos em T2 (R1 também atuará nas seleções de função):

```bash
python run_uxagent_t1.py --mock --task T2 --enable R1,R2,R3,R4 --seed 42
```

Para alterar probabilidades, copie/edite `uxagent_mechanisms.json` ou modifique a configuração usada com `--config /caminho/arquivo.json`. Para testar limites determinísticos, use probabilidades `0.0` e `1.0`. A opção `--seed` torna as decisões aleatórias do controlador reproduzíveis. A semente não torna as respostas do LLM necessariamente determinísticas.

Primeiro execute as demonstrações com `--mock`, sem custos. Quando os efeitos estiverem claros, repita uma tarefa com Gemini real removendo `--mock` da linha de comando. Exemplo: `python run_uxagent_t1.py --task T2 --enable R2,R3,R4 --seed 42`. Cada ação proposta pode gerar uma chamada à API, e uma sessão pode terminar em falha por efeito intencional de um mecanismo; confira os logs antes de repetir.

## Onde estão os resultados

Cada execução cria `logs/<session-id>.jsonl`. Os eventos registram tarefa, versão/hash da configuração, ação proposta, ação executada, estado verdadeiro e visível, rejeições, erro, oportunidade, resultado externo e origem sintética. O contador `actions_executed` só aumenta para ações aceitas; `actions_proposed` conta tentativas processadas, incluindo rejeições. O log nunca deve receber dados reais de pessoas para os testes com API.

## Limites conhecidos nesta versão

- CLI apenas; ainda não há interface gráfica clicável.
- T1 e T2 são tarefas de calibração sintéticas.
- T3/T4 continuam reservadas para uma validação independente.
- R1 injeta um deslize ao efetivar uma atribuição incompatível na simulação; isso é um mecanismo de teste, não um modelo empiricamente calibrado de erro humano.
- R2 pode tornar impossível concluir a exigência de comunicação quando `send_ping` não está disponível. Isso é intencional para observar a consequência da affordance, mas precisa ser relatado como efeito do cenário manipulado.
- A primeira análise dos logs reais de T2 (configuração v1) mostrou cinco pings na mesma tarefa; na configuração v2, o ping correto é uma oportunidade única e sai do menu após o envio. A integração atual foi verificada com testes unitários e modo mock; o Gemini real deve ser executado novamente com v2 para confirmar que reduz a repetição.
- R3 testa uma oportunidade de atualização por evento de feed; não simula todos os aspectos de percepção/memória humana.
- O modo `--mock` verifica integração e oráculos de modo reproduzível, mas não testa qualidade do Gemini.
- Não coletar participantes nem enviar dados pessoais à API sem o procedimento e a autorização institucional aplicáveis.

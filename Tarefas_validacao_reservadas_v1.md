# Tarefas de validação reservadas v1

**Status:** reservado para validação independente; não usar em prompts, exemplos, calibração ou ajuste de parâmetros.

**Data de congelamento:** 20/10/2026

**Configuração congelada antes da validação:** `uxagent-r1-r4-v2`; os valores dos mecanismos permanecem hipóteses de engenharia até existir fonte humana compatível.

## T3 - Replanejamento após indisponibilidade de integrante

- **Objetivo:** corrigir uma atribuição existente depois que um integrante se torna indisponível.
- **Pré-condições:** plano parcialmente preenchido; a indisponibilidade ocorre depois da observação inicial; existe distribuição alternativa válida.
- **Entradas:** plano parcial, três funções, cartões com capacidades/disponibilidade e atualização no feed.
- **Caminho admissível:** ler o plano e os cartões; atualizar o feed; localizar a atribuição inválida; redistribuir as funções; revisar; confirmar.
- **Sucesso externo:** nenhuma função atribuída ao integrante indisponível; as três funções aparecem exatamente uma vez; capacidades, disponibilidade e dependências são respeitadas; o plano foi revisado e confirmado.
- **Oportunidades de erro:** não atualizar o feed; manter atribuição inválida; duplicar função; deixar função sem responsável; confirmar sem revisão.
- **Cobertura:** R1 e R3.
- **Independência:** usar combinação de integrantes e restrições diferente de T1/T2, sem alterar a manifestação funcional exercitada.

## T4 - Integrar informações de painéis distintos

- **Objetivo:** combinar requisito da missão e atualização do feed para comunicar o próximo passo e confirmar um plano válido.
- **Pré-condições:** o requisito relevante está distribuído entre o painel da missão e o feed; uma atualização ocorre após a primeira leitura; a ordem válida exige integração das duas fontes.
- **Entradas:** dependências da missão, estado parcial do plano e atualização do feed.
- **Caminho admissível:** ler a missão; atualizar o feed; integrar as fontes; definir a ordem; consultar checklist ou ajuda quando disponível; enviar `NEXT_STEP_ACTIVATE_CHECKPOINT`; revisar; confirmar.
- **Sucesso externo:** plano compatível com ambos os painéis; dependências respeitadas; comunicação registrada; plano revisado e confirmado.
- **Oportunidades de erro:** ignorar atualização; não integrar a dependência; omitir comunicação; confirmar estado incompatível; não revisar.
- **Cobertura:** R2, R3 e R4.
- **Independência:** usar distribuição de informação e estrutura de passos diferentes de T2, sem trocar apenas nomes ou valores.

## Regra de uso

T3 e T4 ficam fora do código de calibração atual. Seus resultados somente poderão ser consultados depois que os mecanismos, parâmetros, prompts, avaliador e métricas estiverem congelados. Qualquer alteração após a abertura da validação invalida esta reserva e exige novo conjunto independente. O arquivo contém especificação de tarefa, não resultados humanos nem resultados do agente.

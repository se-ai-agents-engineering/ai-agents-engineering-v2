# Agent Decision Record — Aurora Tecnologia (Assistente Interno)

**Caso:** Assistente de Suporte e Dúvidas Internas do Colaborador (RH, TI e Benefícios)  
**Data:** 29/09/2026 · **Integrantes:** 370578,371243,371243,372929,370875,373548,373201
**Status:** Proposta Aprovada

---

## 1. Contexto

A Aurora Tecnologia busca implementar um assistente de IA para responder dúvidas operacionais e de políticas internas de colaboradores (abrangendo RH, TI e Benefícios). O sistema precisa atender colaboradores com rapidez e precisão, evitando alucinações sobre regras corporativas e desonerando os times de atendimento humano.

**Restrições principais:**
- **Fidelidade estrita aos documentos:** O assistente não deve inventar regras nem assumir premissas fora das políticas vigentes.
- **Detecção de conflitos e lacunas:** Questões sem base documental ou com contradições entre normas devem ser sinalizadas (`nao_sei`).
- **Governança de direitos:** Decisões sobre concessão individual de benefícios não podem ser tomadas por IA.

**Ação irreversível do caso:**  
Confirmar a um colaborador que ele é elegível ou tem direito garantido a um benefício (ex.: auxílio-creche, reembolsos especiais). Se a IA afirmar elegibilidade indevida, gera passivo trabalhista, desgaste com o colaborador e ônus financeiro irreversível. Por isso, análises individuais de elegibilidade devem ser estritamente escaladas para análise humana do RH.

---

## 2. Alternativas consideradas

Números obtidos na rodada de testes sobre os 10 casos de referência (`casos.json`):

| Arquitetura | Acertos | Custo total (10 casos) | p50 (latência) | p95 (latência) | Custo por acerto | Variou entre execuções? |
|---|---|---|---|---|---|---|
| **A · Prompt único** | 9/10 (90%) | US$ 0.03925 | 1.94 s | 3.94 s | US$ 0.00436 | — |
| **B · Workflow determinístico** | 6/10 (60%) | US$ 0.01224 | 1.75 s | 2.71 s | US$ 0.00204 | — |
| **C · Agente em loop** | 9/10 (90%) | US$ 0.05663 | 4.00 s | 6.08 s | US$ 0.00629 | Não (determinístico nos 10 casos com Haiku) |

### Onde cada uma errou, e por quê:

- **Arquitetura A (Prompt Único):**
  - **Errou apenas o `c07` (conflito):** Embora tenha recebido todos os documentos no contexto, o modelo priorizou a informação do documento especializado (`beneficios-vale-refeicao`) e ignorou a discrepância presente no documento geral (`rh-guia-de-integracao`), respondendo em vez de declarar `nao_sei`.
  - **Limitação estrutural:** Apesar do bom índice de acertos no corpus pequeno (12 docs / ~3.200 tokens de entrada fixos por pergunta), **não escala** para grandes volumes de documentos corporativos.
  - **Superioridade em escopo fechado (RH):** Vale destacar que **se a escalabilidade não for a prioridade e o chat for restrito apenas ao uso do RH** (onde o número de documentos é pequeno e estável), **a Arquitetura A se torna superior à C em todos os sentidos**:
    - **Mesma acurácia:** 9/10 acertos (90%), idêntico ao agente;
    - **Mais barata:** Custo total 30% menor que o Agente C (US$ 0.03925 vs US$ 0.05663; custo por acerto US$ 0.00436 vs US$ 0.00629);
    - **Mais que 2x mais rápida:** Latência mediana p50 de 1.94s (contra 4.00s do Agente C);
    - **Complexidade mínima e zero risco operacional:** Apenas 5 linhas de código, 1 única chamada, sem orquestração de ferramentas, sem risco de loops ou de estourar limites de passos.

- **Arquitetura B (Workflow Determinístico):**
  - **Errou `c03`, `c04`, `c07` e `c10` (60% de acerto):**
    - Em **`c03`** (inclusão de dependente) e **`c04`** (divisão de férias), o classificador rotulou erroneamente como `"elegibilidade"` devido a perguntas em primeira pessoa ("posso dividir...", "posso incluir..."), escalando desnecessariamente sem consultar os documentos.
    - Em **`c07`**, por isolar a busca exclusivamente em `beneficios`, nunca teve acesso ao documento conflitante de `rh`.
    - Em **`c10`** (multi-passo), o roteamento determinístico não consegue orquestrar fontes de domínios distintos simultaneamente (licença-paternidade do RH e plano de saúde de Benefícios).

- **Arquitetura C (Agente em Loop):**
  - **Errou apenas o `c07` (conflito):** O agente realizou a busca no tema `beneficios`, encontrou o documento específico que respondeu à dúvida e encerrou a chamada. Por não ter motivo para suspeitar de erro documental no RH, não buscou em temas alheios.
  - **Destaque positivo:** Foi a única capaz de resolver perguntas multi-passo (**`c10`**) navegando dinamicamente entre múltiplos tópicos, manteve precisão em perguntas ambíguas (**`c05`**, **`c06`**) e respeitou o desfecho de escalabilidade humana (**`c09`**).

---

## 3. Decisão

**Adotar a Arquitetura C (Agente em Loop)** com autonomia restrita e ferramentas bem delineadas de busca e escalonamento.

**Justificativa:**  
Dúvidas corporativas reais que cruzam múltiplos domínios (como demonstrado pelo caso `c10`) demandam a flexibilidade do Agente em Loop, especialmente visando a escalabilidade para um corpus com centenas de documentos corporativos. O Workflow (B) se mostrou frágil diante da diversidade de linguagem do colaborador, perdendo 40% das perguntas por classificação rígida. 

*Ressalva importante:* A escolha de C apoia-se estritamente na necessidade de expansão multi-área e escalabilidade de acervo. Se a premissa de negócio for revista e o assistente for destinado **apenas ao RH com corpus controlado**, a **Arquitetura A é categoricamente superior** em performance, custo e simplicidade.

**Escopo de autonomia:**
- **O agente PODE decidir sozinho:** 
  - Quando e quantas buscas realizar para embasar a resposta.
  - O tema (`rh`, `ti`, `beneficios` ou `todos`) e os termos de busca.
  - Se a pergunta está suficientemente respondida para finalizar o atendimento (`responder`) ou se a informação não existe (`nao_sei`).
- **O agente NÃO PODE decidir sozinho:**
  - Conceder ou atestar elegibilidade a benefícios individuais do colaborador. Qualquer verificação de elegibilidade deve invocar obrigatoriamente a ferramenta `escalar_para_rh`.
  - Executar ações operacionais irreversíveis sem confirmação humana.

**Critério de parada do agente:**
- **Máximo de 5 passos (`MAX_PASSOS = 5`)** por atendimento. Se atingir o limite sem desfecho, o agente interrompe a execução e devolve `Resultado("escalar", [], "Limite de etapas atingido; encaminhado para atendimento humano do RH.")`.

---

## 4. Trade-offs assumidos

1. **Custo operacional maior:** A Arquitetura C teve custo total de **US$ 0.05663** nos 10 casos (~4,6x o custo do workflow determinístico B e ~1,4x o da A), gerando mais chamadas por interação.
2. **Latência de resposta superior:** O tempo de resposta mediano (**p50 = 4.00s**, **p95 = 6.08s**) é aproximadamente o dobro da Arquitetura B (p50 = 1.75s). A equipe aceita essa latência em prol da resolução completa em primeiro contato (First Contact Resolution).
3. **Não-determinismo:** Agentes em loop introduzem variabilidade potencial no plano de execução de ferramentas em comparação a pipelines de código estáticos.

---

## 5. Critério de reversão

A equipe reverterá a arquitetura conforme as seguintes condições observadas em homologação ou produção:

1. **Reversão para Arquitetura A (Escopo restrito ao RH / baixa prioridade em escalabilidade):** Se a estratégia corporativa limitar o chat exclusivamente às políticas de **RH** com base documental fixa, migrar para a **Arquitetura A (Prompt Único)**, colhendo menor custo (US$ 0.00436/acerto), menor latência (p50 de 1.94s) e zero complexidade de ferramentas, mantendo os mesmos 90% de acerto.
2. **Reversão para Arquitetura B (Custo excessivo do Agente):** Se o custo médio por acerto do Agente ultrapassar **US$ 0.01500** (mais de 7x o custo do workflow determinístico).
3. **Reversão para Arquitetura B (Latência extrema):** Se o **p95** ultrapassar **10 segundos**, degradando inaceitavelmente a experiência do colaborador no chat.
4. **Reversão para Arquitetura B (Margem de acurácia estreita):** Se, após refinamento do prompt do classificador e inclusão de busca global no Workflow (B), a diferença de acertos entre o Agente (C) e o Workflow (B) for **menor ou igual a 1 pergunta** em uma bateria de testes ampliada (50+ casos).



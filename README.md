# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Entrega do desafio. Fork de
[devfullcycle/mba-ia-pull-evaluation-prompt](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).

O projeto faz pull de um prompt de baixa qualidade do LangSmith Prompt Hub
(`leonanluppi/bug_to_user_story_v1`), reescreve com técnicas de prompt
engineering, publica a versão otimizada como prompt público
(`ricardosabaini/bug_to_user_story_v2`) e avalia com as 5 métricas LLM-as-Judge
sobre os 15 exemplos do dataset.

Gerador `gpt-4o-mini`, juiz `gpt-4o`, `temperature=0`. Os arquivos marcados como
"não alterar" no enunciado (`src/evaluate.py`, `src/metrics.py`, `src/utils.py` e
`datasets/bug_to_user_story.jsonl`) seguem intactos.

```
✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

- [A) Técnicas Aplicadas (Fase 2)](#a-técnicas-aplicadas-fase-2)
- [B) Resultados Finais](#b-resultados-finais)
- [C) Como Executar](#c-como-executar)

---

# A) Técnicas Aplicadas (Fase 2)

Quatro técnicas, declaradas nos metadados do YAML:

```yaml
techniques_applied:
  - Role Prompting
  - Few-shot Learning
  - Chain of Thought
  - Skeleton of Thought
```

## 1. Role Prompting

**Por quê:** o v1 usava persona genérica e, pior, pedia "tarefas para
desenvolvedores", o que empurrava a saída para o artefato errado. A persona
precisa dizer duas coisas: quem escreve e qual artefato sai.

**Como apliquei** (abertura do `system_prompt`):

```text
Você é um Product Owner sênior especializado em refinamento de backlog ágil.
Você recebe relatos de bug e os reescreve como User Story pronta para a sprint,
sempre na ótica de quem usa o produto, nunca como tarefa técnica de desenvolvedor.
```

A segunda frase é a que faz trabalho de verdade: "nunca como tarefa técnica de
desenvolvedor" é a negação literal do que o v1 pedia.

## 2. Chain of Thought

**Por quê:** a decisão que define toda a resposta é classificar o relato em
simples, médio ou complexo, e ela precisa acontecer **antes** de o modelo começar
a escrever. Sem isso ele escolhe o formato no meio da geração e mistura os três.
O raciocínio fica proibido na saída, porque nenhuma das 15 referências mostra
raciocínio e o juiz de Precision pune conteúdo que sobra.

**Como apliquei** (bloco `RACIOCÍNIO`, trecho):

```text
RACIOCÍNIO (faça mentalmente, passo a passo, e nunca escreva na resposta)

1. Conte as linhas do relato. A contagem decide o nível:
   - 1 ou 2 linhas: SIMPLES.
   - de 3 a 20 linhas: MÉDIO.
   - mais de 20 linhas, com dois ou mais problemas numerados: COMPLEXO.
   Só a contagem de linhas decide o nível.
2. Identifique quem é afetado, o que essa pessoa quer poder fazer e qual o valor.
3. Liste os cenários verificáveis: contexto, ação e resultado esperado.
...
7. Escreva apenas a saída final, no formato do nível identificado.
```

O critério é numérico e fechado porque a versão qualitativa vazava: relatos
médios com números e maiúsculas eram promovidos a complexo, e a resposta saía com
seções que a referência não tinha.

## 3. Skeleton of Thought

**Por quê:** as 15 referências do dataset não seguem um formato único. Medindo
elas, aparecem três, escolhidos pela complexidade do relato: cerca de 400 chars e
5 bullets nos simples, 660 a 960 chars com seções extras nos médios, e 3600 a
5760 chars com tasks técnicas nos complexos. Um esqueleto só não serve, então o
prompt carrega os três e o CoT escolhe.

**Como apliquei** (esqueleto do nível simples, o mais curto dos três):

```text
FORMATO DO NÍVEL SIMPLES

Como um [persona específica com o contexto de uso], eu quero [ação desejada],
para que [valor para a pessoa ou para o negócio].

Critérios de Aceitação:
- Dado que [contexto inicial]
- Quando [ação da pessoa]
- Então [resultado esperado]
- E [verificação adicional]
- E [verificação adicional]

Exatamente 5 bullets, na ordem Dado / Quando / Então / E / E, em uma única
seção. Se você escreveu mais de 5 bullets, apague o excedente.
```

Os placeholders usam colchetes e não chaves por decisão de projeto: o
`ChatPromptTemplate` trataria uma chave como variável de entrada e quebraria a
avaliação com `KeyError`. O `system_prompt` tem zero chaves, e `input_variables`
é exatamente `['bug_report']`.

## 4. Few-shot Learning (obrigatória)

**Por quê:** nenhuma instrução em prosa ensinou o modelo a parar em 5 bullets no
nível simples nem a nomear a segunda seção do nível médio. Exemplo ensina isso em
uma leitura.

**Como apliquei:** 6 exemplos completos de entrada e saída, cada um cobrindo um
caso que o prompt errava:

| Exemplo | Nível | O que ele ensina |
|---|---|---|
| 1 | simples | o formato base, 5 bullets |
| 2 | simples | relato **com números** continua em 5 bullets, sem virar médio |
| 3 | médio | segunda seção de acessibilidade |
| 4 | médio | segunda seção nomeada pelo gatilho do relato |
| 5 | médio | integração: caso em que a segunda seção **não** existe |
| 6 | médio | dois atores concorrendo sobre o mesmo recurso |

Trecho real do Exemplo 1:

```text
### Exemplo 1 (nível SIMPLES)

Entrada:
Ao clicar em "Esqueci minha senha", o email de recuperação não chega.

Saída:
Como um usuário que perdeu o acesso à minha conta, eu quero receber o email de
recuperação de senha, para que eu possa voltar a usar o sistema sem abrir um
ticket de suporte.

Critérios de Aceitação:
- Dado que estou na tela de login
- Quando clico em "Esqueci minha senha" e informo meu email cadastrado
- Então devo receber o email de recuperação em até 2 minutos
- E o link do email deve permitir definir uma nova senha
- E devo ver na tela a confirmação de que o email foi enviado
```

Os bugs dos exemplos foram escritos por mim, não copiados do dataset: colar um
exemplo do dataset daria nota quase perfeita nele, mas arriscaria o modelo
importar aquele conteúdo para os exemplos vizinhos, o que o juiz de Precision
pune como alucinação.

## Onde estão os demais requisitos do prompt otimizado

| Requisito do enunciado | Onde está no `bug_to_user_story_v2.yml` |
|---|---|
| Instruções claras e específicas | blocos `RACIOCÍNIO` e `FORMATO DO NÍVEL ...` |
| Regras explícitas de comportamento | bloco `REGRAS`, com 16 regras |
| Exemplos de entrada/saída (Few-shot) | bloco `EXEMPLOS`, com 6 exemplos |
| Tratamento de edge cases | regras nomeadas dentro do bloco `REGRAS`: dado essencial ausente no relato (sai entre colchetes na saída), relato sem número nenhum (exige paridade qualitativa em vez de meta inventada), bug sem ator humano (a persona vira "Como o sistema de ..."), e relato de integração (o segundo bloco do formato médio não existe) |
| System vs User Prompt | `system_prompt` com toda a instrução, `user_prompt` apenas com a variável de entrada |

---

# B) Resultados Finais

## Link público do dashboard do LangSmith

Todos abrem **sem login**.

| O que | Link |
|---|---|
| **Dataset com 15 exemplos + experimento com as notas** | https://smith.langchain.com/public/b1b50576-9889-4351-8126-398830b26cb3/d |
| Tracing detalhado, exemplo **simple** | https://smith.langchain.com/public/07b169ee-c1c7-4b23-8540-70c6041960a9/r |
| Tracing detalhado, exemplo **medium** | https://smith.langchain.com/public/c74d2c7e-413a-41c2-bc0f-3ab54b63e187/r |
| Tracing detalhado, exemplo **complex** | https://smith.langchain.com/public/bbe9e000-a5a7-4bd3-8b3d-f384f2e57fae/r |
| Prompt v2 público no Prompt Hub | https://smith.langchain.com/hub/ricardosabaini/bug_to_user_story_v2 |

## Screenshots das avaliações

**As 5 métricas do experimento, todas acima de 0.8:**

![Experimento com as 5 métricas](evidencias/capturas/01-experimento-5-metricas.png)

**Dataset de avaliação com os 15 exemplos:**

![Dataset com 15 exemplos](evidencias/capturas/02-dataset-15-exemplos.png)

**Nota por exemplo, 15 linhas com as 5 métricas cada:**

![Notas por exemplo](evidencias/capturas/03-notas-por-exemplo.png)

## Tabela comparativa: v1 x v2

Mesma régua nos dois lados: mesmo dataset de 15 exemplos, mesmo gerador
`gpt-4o-mini` com `temperature=0`, mesmos 3 juízes `gpt-4o` de `src/metrics.py`.

| Métrica | v1 (original) | v2 (otimizado) | Ganho |
|---|---|---|---|
| Helpfulness | 0.8750 ✓ | **0.8823 ✓** | +0.0073 |
| Correctness | 0.8111 ✓ | **0.8412 ✓** | +0.0301 |
| F1-Score | **0.7555 ✗** | **0.8111 ✓** | **+0.0556** |
| Clarity | 0.8833 ✓ | **0.8933 ✓** | +0.0100 |
| Precision | 0.8667 ✓ | **0.8713 ✓** | +0.0046 |
| **Média geral** | **0.8383** | **0.8598** | **+0.0215** |
| **Status** | **REPROVADO** (F1) | **APROVADO** | |

Duas observações honestas sobre esses números:

1. **Medido com esses modelos, o v1 reprova em uma métrica só, o F1.** Está longe
   dos 0.45 a 0.52 ilustrativos do enunciado. A explicação é que o `gpt-4o-mini`
   produz uma user story razoável mesmo com instrução pobre, e Clarity e
   Precision avaliam qualidades que não dependem do formato da referência. O que
   o v1 não entrega é cobertura do conteúdo, que é o que o F1 mede. Por isso a
   otimização se concentrou no F1, e é lá que está quase todo o ganho.
2. O v1 foi medido com um script auxiliar que reproduz o cálculo do `evaluate.py`
   e troca apenas o prompt avaliado, porque o `evaluate.py` só aceita
   `bug_to_user_story_v2` como alvo. Nenhum arquivo protegido foi tocado.

## Iterações

Cada iteração é uma rodada completa de avaliação: edita o YAML, faz push para o
Hub, roda os 15 exemplos e lê as métricas baixas para decidir a mudança seguinte.
São 15 exemplos e 60 requisições por rodada.

| # | O que mudou | Helpful. | Correct. | F1 | Clarity | Precision | Média | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | v2 inicial: as 4 técnicas, os 3 esqueletos de formato e 2 exemplos few-shot | 0.84 ✓ | 0.77 ✗ | 0.73 ✗ | 0.86 ✓ | 0.82 ✓ | 0.8036 | REPROVADO |
| 2 | bloco de regras explícitas, tabela de expectativas de domínio por tipo de bug e 3º exemplo | 0.85 ✓ | 0.7993 ✗ | 0.77 ✗ | 0.88 ✓ | 0.82 ✓ | 0.8266 | REPROVADO |
| 3 | meta numérica que nunca reaproveita o número ruim do relato, e 4º exemplo, do gatilho de concorrência | 0.86 ✓ | 0.81 ✓ | 0.78 ✗ | 0.88 ✓ | 0.83 ✓ | 0.8315 | REPROVADO |
| 4 | autoconferência de nível nas regras, 5º exemplo, do gatilho de acessibilidade, e volume do nível médio | 0.88 ✓ | 0.83 ✓ | 0.788 ✗ | 0.88 ✓ | 0.88 ✓ | 0.8503 | REPROVADO |
| **5** | **orçamento de bullets alinhado às referências, regra de notificação invertida, 6º exemplo e par contrastivo** | **0.88 ✓** | **0.84 ✓** | **0.8027 ✓** | **0.89 ✓** | **0.87 ✓** | **0.8556** | **APROVADO** |

O prompt cresceu de 7.060 para 22.885 caracteres e de 2 para 6 exemplos few-shot
ao longo dessas iterações. A versão da iteração 5 é a que está publicada no Hub,
e ela foi confirmada em duas rodadas seguintes sem nenhuma alteração no prompt:
F1 0.8111 na rodada publicada acima e F1 0.81 na conferência final da entrega.
São três rodadas aprovadas com `gpt-4o-mini`, o gerador que o enunciado
prescreve.

O que mais moveu a nota foi **injetar conhecimento de domínio** (a tabela de
expectativas, na iteração 2, foi o único ganho agregado que saiu do ruído) e
**transformar regra em exemplo few-shot**: sempre que uma instrução em prosa
virou demonstração, a nota do exemplo-alvo subiu forte, e sempre que a mesma
ideia ficou só descrita, não pegou. O que não funcionou foi tentar casar tamanho
e contagem de bullets com a referência, porque o juiz mede cobertura semântica e
não volume. Um limite de método que vale registrar: `temperature=0` não torna o
`gpt-4o-mini` determinístico, e o ruído entre rodadas no F1 agregado é de ±0.03,
o que explica a rodada de confirmação.

---

# C) Como Executar

## Pré-requisitos

- Python 3.9 ou superior (desenvolvido no 3.13, Windows 11)
- Conta no LangSmith com API key: https://smith.langchain.com
- Conta na OpenAI com API key e crédito: https://platform.openai.com/api-keys
- Custo de uma rodada de avaliação (15 exemplos, 60 requisições): cerca de
  US$ 0,50

## Instalação

```bash
git clone https://github.com/ricardosa1992/mba-ia-pull-evaluation-prompt.git
cd mba-ia-pull-evaluation-prompt

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Configuração do `.env`

```bash
cp .env.example .env
```

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<sua chave do LangSmith>
LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt

# handle do seu workspace no Prompt Hub, sem a barra
USERNAME_LANGSMITH_HUB=<seu username>

OPENAI_API_KEY=<sua chave da OpenAI>
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
```

`USERNAME_LANGSMITH_HUB` é o handle do workspace, não o email. Para descobrir:
publique qualquer prompt no Hub, abra e clique no cadeado.

## Comandos, por fase

Todos rodam a partir da raiz do repositório.

### Fase 1: pull do prompt v1

```bash
python src/pull_prompts.py
```

Puxa `leonanluppi/bug_to_user_story_v1` do Hub e grava
`prompts/bug_to_user_story_v1.yml`, com o `commit_hash` de origem nos metadados.
Sem custo de LLM.

### Fase 2: otimizar o prompt

O `prompts/bug_to_user_story_v2.yml` já está pronto neste repositório. Para
experimentar variações, edite o arquivo direto. O que ele precisa manter:

- `system_prompt`, `user_prompt`, `description`, `version` e
  `techniques_applied` com 2 técnicas ou mais, senão a validação do push reprova;
- o `user_prompt` com exatamente a variável `bug_report`, e nenhuma outra chave
  no arquivo, senão o `evaluate.py` quebra com `KeyError`;
- nenhum `[TODO]`, senão o pytest reprova.

### Fase 3: push público no Prompt Hub

```bash
python src/push_prompts.py
```

Valida o YAML, publica em `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` como
repositório **público**, com descrição, tags e as técnicas no readme, e depois
confirma por API que o prompt está público e que as variáveis voltaram certas.
Sem custo de LLM.

Este passo não é opcional entre uma edição e uma avaliação: o `evaluate.py` puxa
o prompt do Hub, não do arquivo local.

### Fase 4: avaliação

```bash
python src/evaluate.py
```

Cria o dataset `{LANGSMITH_PROJECT}-eval` com os 15 exemplos do `.jsonl` se ainda
não existir, puxa o v2 do Hub, gera as 15 respostas e chama os 3 juízes em cada
uma. **60 requisições, alguns minutos.** Imprime nota por exemplo, as 5 métricas
agregadas, a média e o status.

Sai com código `0` quando as 5 métricas **e** a média ficam em 0.8 ou acima, `1`
quando alguma fica abaixo. O `1` é resultado de avaliação, não falha de execução.

### Fase 5: testes de validação

```bash
pytest tests/test_prompts.py -v
```

Os 6 testes leem o YAML local, não o Hub, então rodam sem rede e sem gastar API.
Saída esperada: `6 passed`.

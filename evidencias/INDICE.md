# Evidências da otimização e avaliação do prompt v2

Material de apoio das Missões 7 (loop de iteração), 8 (evidências no
LangSmith) e 10 (entrega final). O relato analítico completo, com o porquê de cada mudança, está em
`MISSOES.md` na raiz do repositório.

**Comece por `links-publicos.md`:** é lá que estão o link público do dataset com
o experimento aprovado e os 3 traces públicos. As mesmas páginas, em imagem,
estão em `capturas/`.

Os arquivos aqui são **saída bruta de execução**, não editada, para permitir
conferência independente.

## rodadas/

Saída completa de `python src/evaluate.py` em cada iteração. Cada arquivo traz as
notas por exemplo, as 5 métricas agregadas, a média e o status.

| Arquivo | Provider / modelo gerador | F1 | Status |
|---|---|---|---|
| `tentativa-abortada-cota-gemini.txt` | Gemini `gemini-3.6-flash` | inválido | abortada, cota diária de 20 req |
| `iteracao-01-baseline.txt` | OpenAI `gpt-4o-mini` | 0.73 | REPROVADO |
| `iteracao-02.txt` | OpenAI `gpt-4o-mini` | 0.74 | REPROVADO |
| `iteracao-03.txt` | OpenAI `gpt-4o-mini` | 0.77 | REPROVADO |
| `iteracao-04.txt` | OpenAI `gpt-4o-mini` | 0.78 | REPROVADO |
| `iteracao-05.txt` | OpenAI `gpt-4o-mini` | 0.794 | REPROVADO |
| `iteracao-06.txt` | OpenAI `gpt-4o-mini` | 0.765 | REPROVADO |
| `iteracao-07.txt` | OpenAI `gpt-4o-mini` | 0.788 | REPROVADO, melhor com `mini` |
| `iteracao-08.txt` | OpenAI `gpt-4o-mini` | 0.77 | REPROVADO |
| `iteracao-09.txt` | OpenAI `gpt-4o-mini` | 0.77 | REPROVADO |
| `iteracao-10-APROVADA.txt` | OpenAI `gpt-4o` | 0.83 | **APROVADO** |
| `iteracao-10b-APROVADA-confirmacao.txt` | OpenAI `gpt-4o` | 0.82 | **APROVADO** |
| `iteracao-11.txt` | OpenAI `gpt-4o-mini` | 0.78 | REPROVADO, simplificação neutra |
| `iteracao-12-APROVADA-gpt-4o-mini.txt` | OpenAI `gpt-4o-mini` | **0.8027** | **APROVADO** |
| `missao-08-experimento-langsmith.txt` | OpenAI `gpt-4o-mini` | **0.8111** | **APROVADO**, e o experimento publicado |
| `missao-10-conferencia-final.txt` | OpenAI `gpt-4o-mini` | **0.81** | **APROVADO**, conferência final da entrega (Missão 10) |
| `v1-medicao-para-tabela-comparativa.txt` | OpenAI `gpt-4o-mini` | 0.7555 | REPROVADO, é o **prompt v1** medido para a tabela comparativa |

A primeira linha registra por que o provider foi trocado: o `gemini-3.6-flash`,
substituto oficial do `gemini-2.5-flash` do enunciado, tem cota de 20 requisições
por dia no free tier, e uma rodada de avaliação consome 60.

Da iteração 9 para a 10 **o prompt não mudou**: a única alteração foi
`LLM_MODEL`, de `gpt-4o-mini` para `gpt-4o`.

A iteração 11 corta 17% da prosa de instrução do prompt aprovado, sem tocar na
tabela de expectativas nem nos 5 exemplos few-shot. Ela roda com `gpt-4o-mini`,
então compara contra as iterações 1 a 9 e **não** contra a rodada aprovada: o F1
de 0.78 empata com os 0.788 da iteração 7, dentro do ruído de ±0.03. Falta a
rodada com `gpt-4o` para saber se a versão enxuta mantém o `APROVADO`.

O arquivo `missao-08-experimento-langsmith.txt` tem 3 blocos, porque é saída
bruta: a rodada com as notas, uma tentativa de recompartilhar que estourou 409
(`Dataset already shared`, o que motivou tornar o compartilhamento idempotente) e
a execução final dos links. O traceback do meio é esperado, não é falha da
rodada.

A rodada da Missão 8 usa o mesmo prompt da iteração 12, sem nenhuma alteração, e
é a **rodada de confirmação** que faltava: F1 0.8111 contra 0.8027, as 5 métricas
acima de 0.8 nas duas. Ela é a saída do `publica_experimento.py`, então além das
notas no terminal ela deixa um experimento de verdade no LangSmith.

A rodada da Missão 10 é a **conferência final da entrega**: `python
src/evaluate.py` sem nenhuma alteração no prompt nem no `.env`, saída bruta e
`EXIT_CODE=0` no fim do arquivo. F1 0.81, média 0.8535, `STATUS: APROVADO`. Com
ela são **três rodadas independentes** aprovando a mesma versão do prompt com
`gpt-4o-mini`, o que tira a aprovação da dependência da margem de +0.0027 que a
iteração 12 tinha sozinha.

A última linha é a **única rodada do prompt v1**, feita na Missão 9 para a tabela
comparativa do entregável B. Ela usa a mesma régua das rodadas do v2: mesmo
dataset, mesmo gerador `gpt-4o-mini`, mesmos juízes `gpt-4o`. O resultado
surpreende: o v1 reprova em **uma só métrica**, o F1 (0.7555), e passa nas outras
quatro, com média geral 0.8383. Nada parecido com os 0.45 a 0.52 ilustrativos do
enunciado. A leitura está no README, seção B.3.

A iteração 12 parte da 11 e **passa com `gpt-4o-mini`**, o gerador do enunciado,
o que torna o desvio de modelo desnecessário. Ela nasceu de duas fontes de
evidência novas: o `reasoning` do juiz de F1, recuperado com `diag_f1.py`, e um
levantamento estrutural das 15 referências (seções, bullets por seção,
vocabulário). Atenção à margem: F1 0.8027 contra corte de 0.8000, com ruído de
rodada de ±0.03. A confirmação veio na rodada da Missão 8 (F1 0.8111).

## versoes-do-prompt/

Uma cópia de `prompts/bug_to_user_story_v2.yml` por iteração, para acompanhar a
evolução. `v2-iteracao-07.yml` é a versão **aprovada**, com `gpt-4o`.
`v2-iteracao-11.yml` é a versão **simplificada**, neutra em nota.
`v2-iteracao-12.yml` é a versão **aprovada com `gpt-4o-mini`** e a que está
publicada no Hub hoje (commit `38ad5dba`).

## ferramentas/

Scripts auxiliares escritos para diagnosticar as notas. Ficam fora de `src/`
porque a estrutura de `src/` é definida pelo enunciado, e nenhum deles é
necessário para executar o projeto.

| Script | Para que serve |
|---|---|
| `smoke_test.py` | valida ambiente, credenciais e acesso aos modelos antes de gastar API |
| `map_ordem.py` | descobre a ordem em que `list_examples` devolve os exemplos e casa cada posição com o nível de complexidade do JSONL. A API devolve em ordem **inversa** à do arquivo |
| `analisa_log.py` | cruza o log do `evaluate.py` com esse mapa e produz média por nível de complexidade |
| `diag_f1.py` | recupera `precision` e `recall` separados e o `reasoning` dos juízes, que o `evaluate.py` descarta |
| `mede_refs.py`, `mede_secoes.py` | medem as 15 referências em bullets, seções e palavras por bullet |
| `shape3.py`, `dump.py` | comparam a saída gerada com a referência, por seção e integralmente |
| `mutation_check.py` | quebra o prompt de propósito e confirma que os 6 testes do pytest reprovam |
| `publica_experimento.py` | roda o dataset com `langsmith.evaluation.evaluate`, anexa as 5 notas e o `reasoning` do juiz a cada exemplo e publica os links. É o que o `evaluate.py` não faz |
| `captura_paginas.py` | abre os links públicos no Chrome headless, sem login, e salva as 6 imagens da entrega em `capturas/` |
| `mede_v1.py` | mede o prompt v1 nas mesmas 5 métricas, com a mesma régua das rodadas do v2, para a tabela comparativa do entregável B. O `evaluate.py` só aceita o v2 como alvo |
| `exemplo-de-saida-diag_f1.txt` | uma execução real do `diag_f1.py`, mostrando o tipo de diagnóstico obtido |

## links-publicos.md e experimento-publicado.json

Saída da Missão 8. O `.md` é para ler: links públicos, tabela das 5 métricas e o
status. O `.json` é o estado bruto da publicação (nota de cada exemplo, `run_id`,
`example_id`, tokens de compartilhamento), usado pelo `--so-links` para refazer
os links sem pagar outra rodada.

## capturas/

As 6 imagens exigidas pela entrega, geradas por `ferramentas/captura_paginas.py`
a partir dos links públicos, em sessão sem login. `capturas/README.md` diz o que
cada uma mostra. Ficam em `capturas/` e não em `screenshots/` de propósito: o
`.gitignore` do projeto ignora `screenshots/`, então nada precisou ser alterado
nele.

| Arquivo | O que mostra |
|---|---|
| `01-experimento-5-metricas.png` | aba Experiments, as 5 médias do experimento |
| `02-dataset-15-exemplos.png` | aba Examples, os 15 exemplos do dataset |
| `03-notas-por-exemplo.png` | tabela do experimento, 15 linhas com as 5 notas |
| `04-trace-simple.png` | trace do exemplo simple (posição 1) |
| `05-trace-medium.png` | trace do exemplo medium (posição 6) |
| `06-trace-complex.png` | trace do exemplo complex (posição 13) |

## O que NÃO está aqui

Nada mais pendente. As seções A, B e C, que eram a última lacuna, estão no
[`README.md`](../README.md) da raiz, e o enunciado original do desafio foi
preservado em `DESAFIO.md`.

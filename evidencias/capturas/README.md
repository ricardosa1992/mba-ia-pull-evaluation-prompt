# Capturas da entrega

Imagens geradas por `evidencias/ferramentas/captura_paginas.py`, que abre
os links publicos de `evidencias/links-publicos.md` no Chrome headless,
**sem nenhum login**. Rodar o script de novo refaz todas elas.

Experimento: `v2-iteracao-12-final-2a7ef724`
Prompt: `ricardosabaini/bug_to_user_story_v2`, commit `38ad5dba`

| Arquivo | O que mostra |
|---|---|
| `01-experimento-5-metricas.png` | aba Experiments, com as 5 medias do experimento |
| `02-dataset-15-exemplos.png` | aba Examples, com os 15 exemplos do dataset |
| `03-notas-por-exemplo.png` | tabela do experimento: 15 linhas com as 5 notas cada |
| `04-trace-simple.png` | trace do exemplo simple (posicao 1 no .jsonl) |
| `05-trace-medium.png` | trace do exemplo medium (posicao 6 no .jsonl) |
| `06-trace-complex.png` | trace do exemplo complex (posicao 13 no .jsonl) |

Duas observacoes para quem for olhar as imagens:

1. A run raiz aparece com o nome **Target**. E o nome que o runner do
   `langsmith.evaluation.evaluate` da para a funcao alvo; o prompt de
   verdade esta no filho `ChatOpenAI` e na descricao do experimento.
2. O cabecalho da aba Experiments mostra a media do servidor, que conta
   14 das 15 notas por uma estatistica materializada desatualizada. As 15
   linhas com nota estao todas em `03-notas-por-exemplo.png`. As duas
   contas passam de 0.8; a divergencia esta explicada em
   `links-publicos.md`.

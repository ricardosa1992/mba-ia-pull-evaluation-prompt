# Links publicos da entrega (Missao 8)

Gerado por `evidencias/ferramentas/publica_experimento.py` em 2026-08-30T14:11:02+00:00.

## Experimento com as notas

- Nome: `v2-iteracao-12-final-2a7ef724`
- Prompt: `ricardosabaini/bug_to_user_story_v2`, commit `38ad5dba`
- Gerador `gpt-4o-mini`, juiz `gpt-4o`, temperature 0
- Link interno (exige login): https://smith.langchain.com/o/cca263ff-b148-4600-94bb-7183ff48d4c9/datasets/fb962127-71df-4b2e-9e05-9360ccd29791/compare?selectedSessions=c095f0f1-a5c3-4e6b-83ba-fc81f6b27db7

| Metrica | Media | Corte 0.8 |
|---|---|---|
| helpfulness | 0.8823 | OK |
| correctness | 0.8412 | OK |
| f1_score | 0.8111 | OK |
| clarity | 0.8933 | OK |
| precision | 0.8713 | OK |
| **media geral** | **0.8598** | OK |

Status: **APROVADO**

## Dataset publico (15 exemplos + experimentos)

https://smith.langchain.com/public/b1b50576-9889-4351-8126-398830b26cb3/d

A pagina abre sem login. Mostra os 15 exemplos do dataset e a aba de
experimentos rodados sobre ele, cada um com as 5 notas por exemplo.

### Sobre o agregado do cabecalho

A tabela acima e calculada aqui a partir das 15 notas de cada
exemplo. O numero que o LangSmith mostra no cabecalho do experimento e
uma estatistica materializada do servidor e ficou com n menor:

| Metrica | n do servidor | media do servidor | media calculada |
|---|---|---|---|
| helpfulness | 14 | 0.8829 | 0.8823 |
| correctness | 14 | 0.8425 | 0.8412 |
| f1_score | 14 | 0.8157 | 0.8111 |
| clarity | 14 | 0.8964 | 0.8933 |
| precision | 14 | 0.8693 | 0.8713 |

As notas dos 15 exemplos estao todas anexadas e visiveis linha a linha
na tabela do experimento; a diferenca esta so no agregado do cabecalho.
Nas duas contas todas as metricas ficam acima de 0.8.

## Traces publicos, um por nivel de complexidade

| Nivel | Posicao no .jsonl | Link |
|---|---|---|
| simple | 1 | https://smith.langchain.com/public/07b169ee-c1c7-4b23-8540-70c6041960a9/r |
| medium | 6 | https://smith.langchain.com/public/c74d2c7e-413a-41c2-bc0f-3ab54b63e187/r |
| complex | 13 | https://smith.langchain.com/public/bbe9e000-a5a7-4bd3-8b3d-f384f2e57fae/r |

Cada trace mostra a chamada completa: prompt vindo do Hub, entrada,
saida gerada e as notas anexadas.

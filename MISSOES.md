# Missões do Desafio: Pull, Otimização e Avaliação de Prompts

Arquivo de gestão do desafio. Cada missão é uma fatia vertical: sai de um estado
funcional e chega em outro estado funcional, com critério de aceite verificável.

**Como usar:** eu implemento uma missão por vez, somente quando você pedir.
Ao concluir, marco o checkbox e atualizo a tabela de status.

---

## Painel de status

| # | Missão | Entrega principal | Status |
|---|--------|-------------------|--------|
| 0 | Ambiente e credenciais | venv + `.env` + smoke test | [x] Concluída |
| 1 | Pull do prompt v1 | `src/pull_prompts.py` + `prompts/bug_to_user_story_v1.yml` | [x] Concluída |
| 2 | Diagnóstico do v1 | análise defeito -> métrica (rascunho) | [x] Concluída |
| 3 | Prompt otimizado v2 | `prompts/bug_to_user_story_v2.yml` | [x] Concluída |
| 4 | Testes de validação | `tests/test_prompts.py` (6 testes verdes) | [x] Concluída |
| 5 | Push público no Hub | `src/push_prompts.py` + prompt publicado | [x] Concluída |
| 6 | Avaliação baseline | 1a rodada de métricas registrada | [x] Concluída |
| 7 | Loop de iteração | **todas as 5 métricas >= 0.8** | [x] Concluída (iteração 12, com `gpt-4o-mini`, confirmada na rodada da Missão 8) |
| 8 | Evidências no LangSmith | dataset + traces + link público | [x] Concluída |
| 9 | README de entrega | seções A, B e C | [x] Concluída (enunciado movido para `DESAFIO.md`, v1 medido de verdade) |
| 10 | Entrega final | repo público + checklist de aceite | [x] Concluída (3ª rodada aprovada, checklist fechado) |

---

## Restrições técnicas descobertas na leitura do código

Fatos que condicionam as missões. Não são suposições, saíram dos arquivos prontos.

1. **`evaluate.py` puxa o prompt do Hub, não do arquivo local.**
   Ele monta `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` e faz `hub.pull(...)`.
   Consequência: nenhuma mudança no YAML tem efeito na nota antes de um novo push.

2. **A variável de entrada tem que ser exatamente `bug_report`.**
   O dataset é `{"inputs": {"bug_report": "..."}}` e o encadeamento é
   `prompt_template | llm` com `chain.invoke(inputs)`. Qualquer variável extra no
   template (`{contexto}`, `{formato}`, etc.) quebra a execução com KeyError.

3. **Chaves literais no prompt precisam ser escapadas (`{{` e `}}`).**
   `ChatPromptTemplate` usa f-string por padrão. Exemplos few-shot com JSON ou
   placeholders literais viram variáveis se não forem escapados.

4. **Só 3 métricas são realmente medidas; 2 são derivadas.**
   `evaluate.py` calcula F1, Clarity e Precision e deriva:
   - `helpfulness = (clarity + precision) / 2`
   - `correctness = (f1 + precision) / 2`

   Logo **Precision entra em 3 das 5 notas**. É a métrica de maior alavancagem.
   As outras 4 funções de `metrics.py` (tone, acceptance_criteria, format,
   completeness) existem mas **não são chamadas** pelo `evaluate.py`.

5. **CORRIGIDA na Missão 2.** A versão original desta restrição dizia que as 15
   referências seguem "um formato fixo e enxuto" e que a v2 deveria imitá-lo sem
   seções extras. **Isso vale só para os 5 bugs simples.** A medição das 15
   referências mostrou três formatos distintos, escolhidos pela complexidade do
   bug: simple com ~400 chars e 5 bullets, medium com ~660 a 960 chars e seções
   extras de critérios e contexto, complex com 3600 a 5760 chars e um documento
   completo com tasks técnicas. Detalhe na Parte B da Missão 2.
   O que continua verdadeiro: Clarity avalia "concisão / sem redundância" e
   Precision avalia "foco / não adicionar informações não solicitadas". Ou seja,
   excesso derruba nota nos simples e falta derruba nota nos complexos. A v2 tem
   que acertar o **nível**, não escolher um tamanho único.

6. **Custo por rodada de avaliação:** 15 gerações + 45 chamadas de juiz = 60
   requisições. No Gemini free (15 req/min) uma rodada leva alguns minutos e
   consome ~60 das 1500 req/dia. 3 a 5 iterações cabem no free tier.

7. **`validate_prompt_structure` (em `utils.py`, importado pelos testes) espera
   um dict plano** com `description`, `system_prompt`, `version` e
   `techniques_applied` com no mínimo 2 itens. O `v1.yml` é aninhado
   (`bug_to_user_story_v1:` na raiz). Decisão a tomar na Missão 3: o `v2.yml`
   será **plano na raiz**, para casar com esse validador e simplificar os testes.

8. **`.gitignore` ignora `screenshots/`.** O entregável pede screenshots no
   README. Na Missão 8/9 será preciso remover essa linha ou usar outro diretório
   para as imagens.

9. ~~`.env` ainda não existe e não há venv no projeto.~~ Resolvido na Missão 0.

10. **Assinatura real de `hub.push` na versão instalada** (confirmada por
    introspecção, insumo para a Missão 5):
    ```
    hub.push(repo_full_name, object, *, api_url=None, api_key=None,
             parent_commit_hash=None, new_repo_is_public=False,
             new_repo_description=None, readme=None, tags=None) -> str
    ```
    O default é **privado**, então `new_repo_is_public=True` é obrigatório para
    atender o requisito "deixá-lo público". Retorna a URL do commit.

11. **As versões fixadas do `requirements.txt` instalam sem conflito no
    Python 3.13.7.** Não foi preciso relaxar nenhum pin. O
    `langchain-google-genai 2.0.8` emite um `FutureWarning` sobre a
    depreciação do pacote `google.generativeai`, que é ruído e não impede o uso.

12. **O `gemini-2.5-flash` exigido pelo enunciado não é mais chamável por chaves
    novas.** Ele aparece em `list_models()`, mas `generateContent` responde
    `404: This model is no longer available to new users. Please update your code
    to use models/gemini-3.6-flash`. Toda a linha 2.5 está bloqueada
    (`gemini-2.5-flash-lite` dá o mesmo erro); a linha 3.x funciona.
    Modelo adotado: **`gemini-3.6-flash`** para gerar e para avaliar, que é o
    substituto indicado pela própria API. Isso precisa ser documentado no README
    da entrega (Missão 9) como desvio por indisponibilidade, não por escolha.

13. **Não é possível usar provider híbrido sem violar a regra de não alterar
    arquivos prontos.** `get_eval_llm` em `utils.py` chama
    `get_llm(model=EVAL_MODEL)`, que resolve o provider por `LLM_PROVIDER`. Logo
    gerar com Gemini e julgar com `gpt-4o` exigiria editar `utils.py`, que é
    proibido. Provider é uma escolha única para geração e avaliação.

14. **O free tier do `gemini-3.6-flash` e de 20 requisições por DIA, nao 1500.**
    O 429 devolve `quota_id: GenerateRequestsPerDayPerProjectPerModel-FreeTier`
    com `quota_value: 20`. As 1500 req/dia do enunciado valem para o
    `gemini-2.5-flash`, que esta bloqueado para chaves novas (restricao 12). Uma
    rodada de avaliação precisa de 60 requisições, entao **nenhuma rodada completa
    cabe no free tier do 3.6-flash**. A cota é por modelo
    (`PerProjectPerModel`), o que abriria a saída de trocar de modelo Gemini, mas
    a decisão foi trocar de provider: **OpenAI**, com `gpt-4o-mini` para gerar e
    `gpt-4o` para avaliar, que é exatamente o que o enunciado prescreve. Custo
    estimado pelo enunciado: US$ 1 a 5 no desafio inteiro.

15. **A API do LangSmith devolve os exemplos na ORDEM INVERSA do arquivo.**
    Medido com `list_examples`, a mesma chamada que o `evaluate.py` usa: a
    posição 1 do log é a linha 15 do JSONL. Logo o `[1/15]` impresso começa nos
    **3 complexos** e termina nos 5 simples. Mapa: 1-3 complex, 4-10 medium,
    11-15 simple. Sem esse mapa não dá para dizer em que nível a nota caiu, e o
    `metadata.complexity` nao ajuda porque o `create_example` nunca o envia ao
    LangSmith: o casamento tem que ser pelo texto do `bug_report`.

16. **O `evaluate.py` NÃO cria experimento no LangSmith. As notas só existem no
    terminal.** Ele não usa `langsmith.evaluation.evaluate`: é um laço `for` que
    chama `metrics.py` e imprime com `print`. Medido na API depois da rodada
    válida da Missão 6:

    | Verificação | Resultado |
    |---|---|
    | runs tracadas no projeto | 208 (o tracing automático do LangChain funciona) |
    | experimentos ligados ao dataset | **0** |
    | runs com nota (feedback) anexada | **0 de 208** |
    | `reference_example_id` das runs | `None`, não ligam ao exemplo do dataset |

    O `reasoning` dos juízes também é descartado, o que foi o motivo de a Missão 6
    ter precisado do `diag_f1.py` para recuperar precision e recall.

    **Impacto na entrega:** dos 3 itens de "Evidências no LangSmith", o dataset de
    15 exemplos e o tracing de 3 exemplos estão atendidos, mas
    **"Execuções dos prompts v2 com notas >= 0.8" não é atendido**. Sem ação,
    sobra só screenshot de terminal.

    **Saída planejada para a Missão 8:** um script novo e ADITIVO (não altera
    nenhum arquivo protegido) que usa `langsmith.evaluation.evaluate` com o mesmo
    `metrics.py`, produzindo um experimento de verdade: nota por exemplo, o
    `reasoning` do juiz como comentário e agregados no cabeçalho, tudo ligado ao
    dataset. Rodar **uma única vez, depois da Missão 7 aprovar**, para as notas do
    experimento publicado serem as aprovadas e não pagar 60 requisições por
    iteração.

    **RESOLVIDO na Missão 8** por `evidencias/ferramentas/publica_experimento.py`,
    exatamente nesse desenho. Depois da rodada: 15 runs raiz, todas com
    `reference_example_id` preenchido e 5 feedbacks anexados cada uma, dentro de
    um experimento ligado ao dataset.

---

## Missão 0: Ambiente e credenciais

**Objetivo:** deixar o projeto executável e com credenciais válidas.

**Escopo:** `venv/`, `.env`. Nenhum código de produção.

**Passos:**
1. Criar e ativar venv (`python -m venv venv`, `venv\Scripts\activate`).
2. `pip install -r requirements.txt`.
3. Copiar `.env.example` para `.env` e preencher: `LANGSMITH_API_KEY`,
   `LANGSMITH_PROJECT`, `USERNAME_LANGSMITH_HUB` e a chave do provider escolhido
   (`GOOGLE_API_KEY` ou `OPENAI_API_KEY`).
4. Decidir o provider (Gemini free x OpenAI pago) e ajustar `LLM_PROVIDER`,
   `LLM_MODEL` e `EVAL_MODEL`.
5. Rodar um smoke test mínimo: instanciar o `Client()` do LangSmith, listar
   datasets e fazer uma chamada curta no LLM via `get_llm()`.

**Critério de aceite:**
- `pip list` mostra langchain, langsmith e o SDK do provider instalados.
- Smoke test imprime a resposta do LLM e não estoura erro de autenticação.
- `.env` não aparece em `git status`.

**Depende de:** nada.

**Decisão sua:** qual provider usar. Recomendo Gemini free para iterar barato,
já que `EVAL_MODEL=gemini-2.5-flash` funciona como juiz.

### Execução (2026-08-23)

Feito:
- `venv/` criado com Python 3.13.7.
- `pip install -r requirements.txt` concluído sem conflito, todas as versões
  fixadas respeitadas (langchain 0.3.13, langsmith 0.2.7, pydantic 2.10.4,
  langchain-openai 0.2.14, langchain-google-genai 2.0.8, pytest 8.3.4).
- Imports críticos validados: `langchain.hub`, `langsmith.Client`,
  `ChatPromptTemplate`, `ChatOpenAI`, `ChatGoogleGenerativeAI`.
- `.env` criado a partir de `.env.example` e confirmado como ignorado pelo git.
- `LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt` definido. Isso faz o
  `evaluate.py` usar o dataset `mba-ia-pull-evaluation-prompt-eval`.
- Provider: `google`. O modelo do enunciado (`gemini-2.5-flash`) retornou 404
  por indisponibilidade para chaves novas, então `LLM_MODEL` e `EVAL_MODEL`
  foram ajustados para `gemini-3.6-flash` (ver restrição 12). Para trocar para
  OpenAI, basta comentar o bloco `google` e descomentar o bloco `openai` no fim
  do `.env`.
- Smoke test escrito e executado. Ele checa pacotes, variáveis, conexão com o
  LangSmith, uma chamada no LLM, uma no LLM juiz e a integridade dos arquivos
  base (dataset com 15 exemplos confirmado). Não imprime segredos, só presença
  e tamanho das chaves.

Credenciais preenchidas por você e validadas contra as APIs reais:
- `LANGSMITH_API_KEY`: autenticação no LangSmith OK (workspace ainda sem
  datasets, o que é o esperado antes da Missão 6).
- `GOOGLE_API_KEY`: geração e avaliação respondendo com `gemini-3.6-flash`.
- `USERNAME_LANGSMITH_HUB=ricardosabaini`. É esse valor que o `evaluate.py` usa
  para montar `ricardosabaini/bug_to_user_story_v2`, então o push da Missão 5
  precisa publicar exatamente com esse dono.

**Resultado do smoke test: 6 seções OK, exit code 0. Missão 0 concluída.**

O smoke test fica em
`%TEMP%\claude\...\scratchpad\smoke_test.py`, fora do repositório, para não
alterar a estrutura obrigatória do projeto.

---

## Missão 1: Pull do prompt v1 do LangSmith

**Objetivo:** implementar o pull real do Hub e materializar o v1 local.

**Escopo:** `src/pull_prompts.py`, `prompts/bug_to_user_story_v1.yml`.

**Passos:**
1. Implementar `pull_prompts_from_langsmith()`:
   - validar env vars com `check_env_vars(["LANGSMITH_API_KEY"])`;
   - `hub.pull("leonanluppi/bug_to_user_story_v1")`;
   - extrair do `ChatPromptTemplate` retornado a mensagem system, a mensagem
     user, as variáveis de entrada e os metadados disponíveis;
   - montar o dict e gravar com `save_yaml(...)` em
     `prompts/bug_to_user_story_v1.yml`.
2. Implementar `main()` com cabeçalho (`print_section_header`), tratamento de
   erro e código de saída 0/1.
3. Preservar o arquivo v1 atual antes de sobrescrever (cópia de referência ou
   inspeção via `git diff`), porque o v1 versionado tem comentários explicativos
   que se perdem na serialização.

**Critério de aceite:**
- `python src/pull_prompts.py` termina com sucesso e imprime o caminho salvo.
- O YAML gerado contém o `system_prompt` real vindo do Hub e a variável
  `bug_report`.
- `git diff prompts/bug_to_user_story_v1.yml` revisado e consciente.

**Depende de:** Missão 0.

**Risco:** o prompt público pode ter mudado de nome ou ficar inacessível. Se
`hub.pull` retornar 404, registro o erro e sigo com o v1 já versionado no repo
como base de análise. A Missão 2 não fica bloqueada.

### Execução (2026-08-23)

`src/pull_prompts.py` implementado em 73 linhas. `python src/pull_prompts.py`
roda com exit code 0 e é idempotente (rodar duas vezes não muda o arquivo).

O que o Hub devolveu, confirmado por introspecção antes de escrever o código:
- tipo `ChatPromptTemplate` com `input_variables = ['bug_report']`;
- 2 mensagens, `SystemMessagePromptTemplate` e `HumanMessagePromptTemplate`,
  ambas em `template_format: f-string`;
- metadados do Hub: owner `leonanluppi`, repo `bug_to_user_story_v1`,
  commit `2950c33dbd7f...`;
- **o `{bug_report}` está de fato nas duas mensagens.** O defeito central que a
  v2 precisa corrigir é real e veio do Hub, não é invenção do arquivo local.

Comparei campo a campo o conteúdo baixado com o arquivo que acompanhava o
repositório: `system_prompt`, `user_prompt`, `description`, `version`,
`created_at` e `tags` são **idênticos**. Ou seja, o pull está correto contra o
ground truth, o Hub e o boilerplate não divergiram.

Decisões de implementação:
- **Estrutura aninhada preservada** (`bug_to_user_story_v1:` na raiz), igual ao
  arquivo original. A v2 será plana, por causa do `validate_prompt_structure`
  (restrição 7).
- **Bloco `source` acrescentado** com `hub_prompt`, `commit_hash` e `pulled_at`,
  para rastrear qual commit do Hub gerou o arquivo.
- **Representer de string em bloco literal registrado no PyYAML.** Sem isso o
  `save_yaml` de `utils.py` gravaria o `system_prompt` como uma linha única com
  `\n` escapado, ilegível e com diff ruim. Feito no `pull_prompts.py`, sem tocar
  em `utils.py`.

Perdas aceitas e conscientes:
- O `yaml.dump` não preserva comentários, então o cabeçalho de 4 linhas que
  explicava os defeitos intencionais do v1 saiu do arquivo. O conteúdo está no
  histórico do git e o diagnóstico vai virar seção do README na Missão 2/9.
- Os campos `created_at` e `tags` do arquivo original saíram. Eles não vêm do
  Hub, então mantê-los exigiria ler e mesclar o YAML local antes de sobrescrever.
  Trocado por simplicidade: nada lê o v1 programaticamente (os testes leem só a
  v2), e as tags da entrega são definidas no push da v2 (Missão 5).

Descoberta anotada mas não tratada em código, por opção sua: em console Windows
com codepage legado (cp1252) o `print` de `✓` e `❌` estoura
`UnicodeEncodeError`. No PowerShell da máquina o stdout já é utf-8, então não
afeta a execução real. Se aparecer em outro ambiente, a saída é rodar com
`PYTHONUTF8=1`, que vale também para o `evaluate.py`, que imprime os mesmos
símbolos e não pode ser alterado.

---

## Missão 2: Diagnóstico do prompt v1

**Objetivo:** listar por escrito os defeitos do v1, para justificar cada escolha
técnica da v2. Isso é exigido na seção A do README final.

**Escopo:** rascunho de análise, que vira seção do README na Missão 9.

**Passos:**
1. Mapear os defeitos concretos do v1:
   - `{bug_report}` duplicado no system e no user prompt (contexto repetido);
   - persona genérica ("um assistente"), sem senioridade nem domínio;
   - nenhuma definição de formato de saída;
   - zero exemplos (nenhum few-shot);
   - nenhuma regra de comportamento nem tratamento de edge case;
   - system prompt terminando em "User Story gerada:", misturando instrução com
     início de completion.
2. Ligar cada defeito à métrica que ele derruba (F1, Clarity, Precision).

**Critério de aceite:** lista de defeitos com o vínculo defeito -> métrica,
pronta para ser colada no README.

**Depende de:** Missão 1 (ou o v1 versionado, se o pull falhar).

### Execução (2026-08-23)

#### Parte A: os 8 defeitos do v1, ordenados por dano

Lembrando como os juízes pontuam (de `metrics.py`): **F1** mede precision
(quanto do que foi dito é correto e relevante) e recall (quanto do que a
referência tem apareceu); **Clarity** mede organização, linguagem, ausência de
ambiguidade e concisão; **Precision** mede ausência de alucinação, foco no que
foi pedido e correção factual contra a referência.

| # | Defeito | Efeito na saída | Métrica atingida |
|---|---------|-----------------|------------------|
| D1 | **Nenhuma especificação de formato.** O prompt não diz template, não cita "Como um... eu quero... para que...", não pede critérios de aceitação nem define seções. | O modelo inventa um formato diferente a cada bug. Alguns vêm com título, prioridade e severidade que a referência não tem; outros vêm sem a seção de critérios que ela tem. | F1 recall (falta o que a referência tem), F1 precision e Precision/foco (sobra o que ela não tem), Clarity/organização (estrutura varia de exemplo para exemplo) |
| D2 | **Nenhuma adaptação por complexidade.** Instrução única para 15 bugs de 3 tamanhos muito diferentes (ver Parte B). | Ou responde curto em tudo, e perde 10 dos 15 casos por falta de conteúdo, ou responde longo em tudo, e perde os 5 simples por excesso. Não existe resposta de tamanho único que sirva. | F1 recall nos medium/complex, F1 precision e Clarity/concisão nos simple |
| D3 | **Objetivo declarado errado.** O system prompt diz que a meta é "transformar relatos de bugs em **tarefas para desenvolvedores**". | Puxa a saída para linguagem de tarefa técnica ("corrigir validação no endpoint X") quando a referência é uma user story escrita da ótica do usuário final. É um erro de tipo de artefato, não de estilo. | F1 (precision e recall), Precision/correção factual |
| D4 | **Zero exemplos (nenhum few-shot).** | Nada calibra tamanho, tom, granularidade nem quantidade de critérios. Nos 5 bugs simples a referência tem exatamente 5 bullets; o modelo não tem como adivinhar essa convenção. | F1 (forma e granularidade), Clarity/concisão, Precision |
| D5 | **Nenhuma regra de comportamento.** Não proíbe preâmbulo, não proíbe inventar dado ausente, não fixa o idioma, não proíbe repetir o bug. | Aparecem "Claro! Aqui está a user story:", números inventados de usuários afetados, prazos que ninguém mencionou. | Precision/alucinação (é literalmente o critério 1 do juiz) e Precision/foco, Clarity/concisão |
| D6 | **`{bug_report}` duplicado** no system e no user prompt. | O bug chega duas vezes: uma cercada por `---` dentro do system, outra crua como turno do usuário. O modelo às vezes ecoa o relato dentro da resposta, e a separação "system = instrução, user = dado" se perde. | Clarity/redundância, Precision/foco |
| D7 | **Persona genérica.** "Você é um assistente que ajuda a transformar relatos de bugs". Sem senioridade, sem domínio, sem convenção de escrita. | Não ativa o vocabulário de quem escreve user story de verdade (persona afetada, valor de negócio, Dado/Quando/Então). | F1 recall, Clarity/organização |
| D8 | **`User Story gerada:` no fim do system prompt.** É isca de completion colada num prompt de chat. | Em chat model isso não abre a resposta, só faz o modelo às vezes repetir o rótulo como primeira linha da saída. | Precision/foco, Clarity/concisão |

Nota sobre peso: como `helpfulness = (clarity + precision) / 2` e
`correctness = (f1 + precision) / 2`, todo defeito que derruba **Precision**
contamina 3 das 5 notas do relatório. Por isso D5 e D1 valem mais atenção do que
o tamanho do texto deles sugere.

O que o v1 **não** erra, e vale preservar: a variável é `{bug_report}`, então
ele executa sem `KeyError`, e as instruções estão em português, o que já empurra
a saída para o idioma certo.

#### Parte B: o formato alvo, medido nas 15 referências

Não inferi por amostragem, medi as 15. **As referências não têm um formato
único: têm três, escolhidos pela complexidade do bug.**

| Nível | Qtd | Tamanho da referência | Bullets | Estrutura |
|---|---|---|---|---|
| simple | 5 | 389 a 447 chars | exatamente **5** em todas | `Como um..., eu quero..., para que...` + `Critérios de Aceitação:` + 5 bullets Dado/Quando/Então/E/E |
| medium | 7 | 664 a 963 chars | 9 a 13 | o mesmo de cima, mais **uma segunda seção de critérios** (`Critérios Técnicos:`, `Critérios de Prevenção:`, `Critérios de Acessibilidade:`, `Critérios Adicionais para Admins:` ou `Exemplo de Cálculo:`) e **uma seção de contexto** (`Contexto Técnico:`, `Contexto de Segurança:` ou `Contexto do Bug:`) |
| complex | 3 | 3605 a 5756 chars | 40 a 47 | documento completo com cabeçalhos `=== SEÇÃO ===`: linha-resumo da story, `=== USER STORY PRINCIPAL ===` (com `Título:` e `Descrição:`), `=== CRITÉRIOS DE ACEITAÇÃO ===` com **4 grupos rotulados A, B, C, D**, `=== CRITÉRIOS TÉCNICOS ===` (com blocos de código quando cabe), `=== CONTEXTO DO BUG ===` (`Severidade:`, `Impacto`, `Problemas Técnicos:` numerados), `=== TASKS TÉCNICAS SUGERIDAS ===` (numeradas, agrupadas por sprint/fase, com tags tipo `[PERF]`, `[BACKEND]`, `[TESTES]`) |

Invariantes nas 15: todas têm `eu quero` e `para que`; nenhuma usa header
markdown (`#`) nem negrito (`**`). As 12 simple/medium têm a linha literal
`Critérios de Aceitação:`; as 3 complex usam `=== CRITÉRIOS DE ACEITAÇÃO ===`.
Nos medium a persona pode ser não humana (`Como o sistema de e-commerce`) quando
o bug é de backend.

**A complexidade é inferível só do bug report**, e as faixas não se sobrepõem:

| Nível | Entrada | Sinais no texto |
|---|---|---|
| simple | 63 a 85 chars, **1 linha** | uma frase, um problema, sem lista |
| medium | 238 a 322 chars, 6 a 10 linhas | um cabeçalho de detalhe (`Steps to reproduce:`, `Detalhes:`, `Cenário:`, `Observações:`, `Fluxo do bug:`) e uma lista, sobre **um** problema |
| complex | 977 a 2559 chars, 29 a 75 linhas | `PROBLEMAS IDENTIFICADOS/REPORTADOS`, às vezes `CONTEXTO:`, e **vários problemas numerados** em maiúsculas |

#### Parte C: correção de uma premissa minha

A restrição 5 deste arquivo dizia que a estratégia era "imitar o formato enxuto,
sem seções extras, porque tudo que excede a referência derruba Precision".
**Isso está errado e foi corrigido lá.** Vale só para os 5 bugs simples. Nos 7
medium a referência espera seções extras, e nos 3 complex espera um documento de
até 5756 chars com tasks técnicas. Responder enxuto nesses 10 casos derruba F1
recall, que é 2 das 5 notas. Se eu tivesse ido para a Missão 3 com a premissa
antiga, teria otimizado na direção errada e gastado iterações para descobrir.

#### Parte D: o que isso define para a Missão 3

1. O esqueleto de saída não é um, são **três**, escolhidos por complexidade.
2. O **primeiro passo do Chain of Thought passa a ser classificar** o bug em
   simple, medium ou complex, usando os sinais da tabela acima. O CoT deixa de
   ser enfeite e passa a ser o mecanismo que seleciona o formato.
3. O few-shot precisa de **exatamente 3 exemplos, um por nível**, porque os
   níveis não se parecem. Dois exemplos do mesmo nível não ensinam o outro.
4. Tensão a resolver: um exemplo complex completo tem ~5000 chars. Colar os três
   inteiros infla muito o system prompt. Provável saída: simple e medium
   completos, complex como esqueleto de seções em vez de texto integral.
5. A regra "exatamente 5 critérios" vale **só** para o nível simple.

#### Parte E: pendência descoberta para o entregável B

O README pede "tabela comparativa: prompts ruins (v1) vs prompts otimizados
(v2)", mas o `evaluate.py` só avalia `{username}/bug_to_user_story_v2`. Para ter
número real do v1 há duas saídas:
- **(recomendada)** script ad hoc no scratchpad importando `metrics.py`, que mede
  o v1 sem tocar em arquivo protegido e sem sujar o Hub;
- publicar o conteúdo do v1 como `bug_to_user_story_v2`, avaliar e depois
  sobrescrever com a v2 real, o que usa só ferramenta oficial mas deixa um
  commit estranho no histórico do prompt.

Custo em qualquer uma: uma rodada de 60 requisições. Decisão fica para a
Missão 6. Sem isso, a tabela comparativa só pode usar os números ilustrativos do
enunciado, o que é mais fraco como evidência.

---

## Missão 3: Prompt otimizado v2

**Objetivo:** criar `prompts/bug_to_user_story_v2.yml` completo e alinhado ao
formato das referências do dataset.

**Escopo:** `prompts/bug_to_user_story_v2.yml` (arquivo novo).

**Estrutura planejada do YAML (plano na raiz, ver restrição 7):**

```yaml
description: ...
version: "v2"
created_at: "..."
system_prompt: |
  ...
user_prompt: "{bug_report}"
techniques_applied:
  - Role Prompting
  - Few-shot Learning
  - Chain of Thought
  - Skeleton of Thought
tags: [...]
```

**Passos:**
1. **Role Prompting:** persona específica ("Você é um Product Owner sênior
   especialista em refinamento de backlog ágil"). Corrige D7 e D3 da Missão 2.
2. **Few-shot (obrigatório): exatamente 3 exemplos, um por nível de
   complexidade** (simple, medium, complex), porque os três formatos não se
   parecem. Ver Parte B da Missão 2. Chaves escapadas onde houver literal.
3. **Técnica adicional, Chain of Thought:** o passo 1 do raciocínio é
   **classificar o bug** em simple, medium ou complex pelos sinais medidos
   (linhas, tamanho, presença de vários problemas numerados); depois identificar
   persona afetada, ação desejada, valor de negócio e cenários. Instrução
   explícita de **não imprimir** o raciocínio. Aqui o CoT não é enfeite, é o
   mecanismo que seleciona o formato de saída.
4. **Skeleton of Thought: três esqueletos**, um por nível, conforme a Parte B da
   Missão 2. Não existe esqueleto único que sirva para os 15 exemplos.
5. **Regras explícitas:** responder em português; sem preâmbulo e sem comentário
   final; sem header markdown (`#`) e sem negrito (`**`), que nenhuma referência
   usa; não inventar dado ausente no bug; usar o template "Como um... eu
   quero... para que...". A regra de **exatamente 5 critérios vale só no nível
   simple**.
6. **Edge cases:** bug vago ou sem contexto (assumir persona genérica plausível
   sem inventar detalhe); bug com múltiplos problemas (cobrir todos nos
   critérios, uma única story); bug com dado técnico (log, ID, endpoint)
   preservado só quando muda o comportamento esperado; entrada que não é bug
   (responder com pedido curto de esclarecimento).
7. **System vs User:** todas as instruções, exemplos e regras no `system_prompt`;
   o `user_prompt` fica apenas com `{bug_report}`, sem duplicação, corrigindo o
   defeito central do v1.
8. Validação local: carregar o YAML, montar `ChatPromptTemplate`, conferir que
   `input_variables == ["bug_report"]` e renderizar com um bug de teste.

**Critério de aceite:**
- YAML válido, sem nenhum `[TODO]`.
- `input_variables` do template resultante é exatamente `["bug_report"]`.
- `validate_prompt_structure(dados)` retorna `(True, [])`.
- Renderização de teste não estoura KeyError de chave não escapada.

**Depende de:** Missão 2.

### Execução (2026-08-23)

`prompts/bug_to_user_story_v2.yml` criado. System prompt com 7060 chars,
`user_prompt` apenas `{bug_report}`.

Validação estrutural, antes de qualquer chamada de API:
- `validate_prompt_structure` retorna `(True, [])`;
- `input_variables == ['bug_report']`, exatamente o que o dataset injeta;
- **zero chaves `{` ou `}` no system prompt**, o que elimina de vez o risco de
  escape f-string da restrição 3. Foi escolha de projeto: os placeholders do
  esqueleto usam colchetes `[...]`, que o f-string ignora;
- nenhum `TODO`;
- renderização de teste sem erro.

Duas decisões de projeto, ambas com justificativa:

1. **Os 2 exemplos few-shot usam bugs escritos por mim, não bugs do dataset.**
   Colar o exemplo 13 no prompt daria nota quase perfeita nele, porque a resposta
   estaria literalmente no contexto, mas arrisca o modelo importar conteúdo de
   checkout para as respostas dos exemplos 14 e 15, o que o juiz de Precision
   pune como alucinação. Ganharia 1 caso e arriscaria 2.
2. **Nível complexo entra como esqueleto, não como exemplo completo.** Um
   exemplo complexo inteiro tem ~4600 chars e dobraria o prompt. O formato
   complexo é mecânico, então o esqueleto comunica a mesma informação. O que
   viabilizou isso foi uma regra descoberta na medição: nos 3 exemplos
   complexos, **cada problema numerado do relato vira exatamente um grupo
   A/B/C/D de critérios, na mesma ordem**. Vale 3 de 3.

**Checagem de formato com 3 chamadas de API** (1 por nível, exemplos 1, 7 e 13
do dataset), comparando a saída gerada com a referência. Não mede nota, mede
forma. Resultado da primeira rodada: seções exatas nos 3 níveis, zero faltando e
zero sobrando, os 4 grupos A/B/C/D corretos no complexo, abertura com "Como um"
nos 3, e nenhum vazamento do raciocínio. Mas a saída vinha longa demais:

| nível | 1a rodada | referência | desvio |
|---|---|---|---|
| simple | 506 chars | 408 | +24% |
| medium | 1142 chars | 704 | +62% |
| complex | 4713 chars | 3605 | +31% |

E no medium apareceu uma seção `Critérios de Performance:` que a referência do
exemplo 7 não tem. Duas correções, ambas apoiadas no dataset e não só na amostra:
- a regra da seção secundária do medium estava permissiva ("quando o relato
  pedir"). Passou a exigir um segundo aspecto realmente distinto, com instrução
  explícita de pular a seção quando o relato trata de um só aspecto. Base: 2 dos
  7 mediums (exemplos 6 e 7) não têm seção secundária;
- regra nova de concisão: bullet em uma linha, no máximo umas 12 palavras. Base:
  os bullets das 15 referências são curtos.

Segunda rodada, depois das correções:

| nível | 2a rodada | referência | desvio |
|---|---|---|---|
| simple | 430 chars | 408 | +5% |
| medium | 732 chars | 704 | +4% |
| complex | 3758 chars | 3605 | +4% |

A seção espúria do medium desapareceu. Custo total da missão: 6 chamadas de API,
contra as 60 de uma rodada de avaliação.

**Lacuna conhecida, a observar na Missão 6:** no nível complexo a saída tem 31
bullets contra 40 da referência, apesar do tamanho em chars bater. Os bullets
saem em menor número e um pouco mais longos. Se F1 recall vier baixo nos 3
exemplos complexos, a primeira alavanca da Missão 7 é essa, e a segunda é
promover o nível complexo de esqueleto para exemplo few-shot completo.

---

## Missão 4: Testes de validação (pytest)

**Objetivo:** implementar os 6 testes exigidos e ficar verde.

**Escopo:** `tests/test_prompts.py`.

**Passos:**
1. Fixture que carrega `prompts/bug_to_user_story_v2.yml` via `load_prompts`.
2. `test_prompt_has_system_prompt`: campo existe e não está vazio.
3. `test_prompt_has_role_definition`: detecta persona (regex por "você é um/uma"
   mais um cargo como Product Owner, Product Manager ou Analista).
4. `test_prompt_mentions_format`: exige menção a formato Markdown ou ao template
   padrão de user story ("Como um", "Eu quero", "Para que").
5. `test_prompt_has_few_shot_examples`: verifica marcadores de exemplo
   ("Exemplo 1", "Entrada:", "Saída:") com no mínimo 2 ocorrências.
6. `test_prompt_no_todos`: nenhum `[TODO]` ou `TODO` no conteúdo.
7. `test_minimum_techniques`: `techniques_applied` com 2 itens ou mais, usando
   `validate_prompt_structure` como reforço.

**Critério de aceite:** `pytest tests/test_prompts.py -v` com 6 passed, 0 failed.

**Depende de:** Missão 3.

**Nota:** os testes leem o YAML local, não o Hub. São independentes de rede.

### Execução (2026-08-23)

`tests/test_prompts.py` implementado sobre o esqueleto original (mantidos os
imports, o `load_prompts` e a classe `TestPrompts`). Acrescentei uma fixture
`prompt` e uma constante `PROMPT_FILE` resolvida a partir do próprio arquivo de
teste, para o pytest rodar de qualquer diretório.

`pytest tests/test_prompts.py -v`: **6 passed, exit code 0.**

**Checagem de mutação, para provar que os testes detectam falha.** Um teste que
passa de primeira não prova nada. Escrevi um script (no scratchpad) que quebra o
prompt de propósito, em memória, e confirma que o teste correspondente reprova.
As 7 mutações foram todas detectadas:

| Mutação | Teste que reprovou |
|---|---|
| `system_prompt` vazio | has_system_prompt |
| sem definição de persona | has_role_definition |
| persona sem cargo reconhecível | has_role_definition |
| sem formato de saída | mentions_format |
| bloco de exemplos removido | has_few_shot_examples |
| só 1 técnica em `techniques_applied` | minimum_techniques |
| arquivo com `[TODO]` | no_todos |

Detalhe que quase virou bug: **em português, "todos" contém "todo"**. Uma busca
case-insensitive por `todo` daria falso positivo no próprio v2, que tem "todos os
caracteres acentuados" no exemplo few-shot. O teste busca `\bTODO\b` em
maiúsculas, com fronteira de palavra, e também `[TODO]` e `FIXME`.

Outras decisões:
- `test_prompt_no_todos` lê o **arquivo cru**, não o YAML parseado, para pegar
  `TODO` também em comentários. Por isso é o único teste que não usa a fixture.
- `test_minimum_techniques` usa `validate_prompt_structure` como reforço, o que
  mantém vivo o import que já vinha no esqueleto.
- `test_prompt_mentions_format` aceita duas vias, como o enunciado pede: formato
  de User Story padrão (as três partes do template mais a linha de critérios) ou
  menção a Markdown.

Ruído conhecido, não é erro: o Pylance marca `Import "utils" could not be
resolved`. É porque o `sys.path.insert` acontece em tempo de execução, e esse
padrão já vinha do esqueleto do desafio. O pytest resolve normalmente.

---

## Missão 5: Push público no Prompt Hub

**Objetivo:** publicar o v2 no Hub como público, com metadados.

**Escopo:** `src/push_prompts.py`.

**Passos:**
1. Implementar `validate_prompt(prompt_data)` com a mesma regra de
   `validate_prompt_structure` (campos obrigatórios, sem TODO, 2+ técnicas).
2. Implementar `push_prompt_to_langsmith(prompt_name, prompt_data)`:
   - montar `ChatPromptTemplate.from_messages([("system", ...), ("human", ...)])`;
   - `hub.push(f"{username}/bug_to_user_story_v2", template, ...)` com o flag de
     repositório público e descrição, tags e técnicas nos metadados (confirmar a
     assinatura exata na versão instalada do `langsmith==0.2.7` antes de chamar);
   - retornar True/False e imprimir a URL do commit.
3. Implementar `main()`: validar env (`LANGSMITH_API_KEY`,
   `USERNAME_LANGSMITH_HUB`), carregar o YAML, validar, dar push, sair 0/1.
4. Conferir no dashboard que o prompt está visível e público.

**Critério de aceite:**
- `python src/push_prompts.py` imprime sucesso e a URL do prompt.
- O prompt abre em janela anônima, provando que está público.
- O nome é exatamente `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`, igual ao
  que o `evaluate.py` monta.

**Depende de:** Missões 3 e 4.

### Execução (2026-08-23)

`src/push_prompts.py` implementado em ~135 linhas. Rodou com exit code 0.

**Prompt publicado:** `ricardosabaini/bug_to_user_story_v2`
URL pública: https://smith.langchain.com/hub/ricardosabaini/bug_to_user_story_v2
Primeiro commit: `b0ea741c`

Verificado por API, não por suposição:
- `is_public: True`
- `system_prompt` e `user_prompt` voltam do Hub **byte a byte idênticos** ao YAML
  local (7060 chars nos dois lados);
- `input_variables` no Hub é `['bug_report']`, que é exatamente o que o
  `evaluate.py` injeta;
- description, tags e readme com as 4 técnicas gravados. O LangSmith acrescenta
  sozinho uma tag `ChatPromptTemplate` às 5 minhas.

**Leitura do código-fonte da lib antes de publicar**, porque push é ação pública
e praticamente irreversível. Duas descobertas que mudam o que eu faria:

1. **`is_public=True` vale também em atualização.** O nome `new_repo_is_public`
   do `hub.push` sugere que só se aplica na criação, mas ele é repassado como
   `is_public` para `client.push_prompt`, que chama `update_prompt(is_public=...)`
   quando o repo já existe. Ou seja, os re-pushes da Missão 7 não vão
   privatizar o prompt nem apagar os metadados.
2. **`parent_commit_hash=None` é seguro.** O `hub.push` sobrescreve o default
   `"latest"` do `push_prompt` com `None`, o que parecia risco de quebrar o
   segundo push. Mas o `create_commit` trata `None` e `"latest"` do mesmo jeito,
   resolvendo para o último commit. O caminho de atualização funciona.

Decisões de implementação:
- **`validate_prompt` reusa `validate_prompt_structure` e acrescenta uma
  checagem própria:** que o template compile e que `input_variables` seja
  exatamente `['bug_report']`. Sem isso a função seria duplicata do utils. Com
  isso ela pega o único erro capaz de fazer a Missão 6 falhar depois de 60
  chamadas de API. Testado por mutação: com `user_prompt` contendo
  `{bug_report} e {contexto}`, a validação reprova e o push é cancelado.
- **Verificação pós-push dentro do `main`:** um `get_prompt` para confirmar
  `is_public` e um `hub.pull` para confirmar as variáveis. Duas chamadas sem LLM
  que transformam "espero que esteja público" em fato.
- **As técnicas vão no `readme`**, não nas tags. Tag com espaço ("Role
  Prompting") fica ruim, e o readme aparece na página do prompt no Hub, o que
  atende melhor o requisito "metadados (tags, descrição, técnicas utilizadas)".
- Não testei re-push duplicado de propósito: criaria um commit redundante no
  histórico só para confirmar algo que o código-fonte já garante. A Missão 7
  exercita esse caminho naturalmente, com mudança real.

---

## Missão 6: Avaliação baseline

**Objetivo:** primeira medição real, sem tocar em `evaluate.py` nem `metrics.py`.

**Escopo:** execução e registro de resultados. Nenhum arquivo pronto alterado.

**Passos:**
1. `python src/evaluate.py`.
2. Confirmar que o dataset `{LANGSMITH_PROJECT}-eval` foi criado com 15 exemplos.
3. Registrar as 5 notas e a média na tabela de iterações (Iteração 1).
4. Para as métricas abaixo de 0.8, ler o `reasoning` dos juízes no tracing do
   LangSmith e anotar as causas concretas (verbosidade, critérios demais, persona
   genérica, informação inventada, etc.). Separar o diagnóstico **por nível de
   complexidade**: uma nota baixa média pode ser "ótimo nos 5 simples, péssimo
   nos 3 complexos", e a correção é diferente em cada caso.
5. Decidir se vale medir o v1 para a tabela comparativa do entregável B
   (ver Parte E da Missão 2). Custo: mais 60 requisições.

**Critério de aceite:** rodada concluída, 5 notas registradas e lista de causas
priorizadas por impacto, lembrando que Precision pesa em 3 notas.

**Depende de:** Missão 5.

### Execução, tentativa 1 (2026-08-23): abortada por cota, rodada descartada

`python src/evaluate.py` rodou e **falhou por esgotamento de cota diária do
Gemini**, não por qualidade do prompt. Ver restrição 14.

O que deu certo e continua valendo:
- dataset `mba-ia-pull-evaluation-prompt-eval` **criado com os 15 exemplos**
  (critério de aceite 2 desta missão, já atendido e não precisa repetir);
- `hub.pull` do `ricardosabaini/bug_to_user_story_v2` carregou sem erro, provando
  que o push da Missão 5 é utilizável pelo `evaluate.py`;
- tracing ativo (`LANGSMITH_TRACING=true`), então as runs ficaram registradas.

**Por que os números impressos foram descartados.** O `metrics.py` devolve
`{"score": 0.0}` quando a chamada do juiz estoura, e o `evaluate.py` soma esse
zero na média. Foram **17 falhas de juiz** viradas 0.00 e 10 exemplos cujo
`answer` nem foi gerado. O relatório imprimiu `MÉDIA GERAL: 0.5016` e REPROVADO
nas 5 métricas, mas isso mede a cota do Gemini, não o prompt. Registrar 0.50 na
tabela de iterações seria registrar ficção, então a linha da Iteração 1 segue
vazia.

**O que a rodada morta entregou de graça.** Pela restrição 15, as posições 1 a 3
do log são os **3 exemplos complexos**, e foram justamente as que rodaram antes
da cota acabar:

| pos | nível | F1 | Clarity | Precision |
|---|---|---|---|---|
| 1 | complex | 0.89 | 1.00 | 1.00 |
| 2 | complex | 0.89 | 0.99 | 1.00 |
| 3 | complex | 0.92 | 1.00 | juiz estourou |

Isso responde à **lacuna conhecida deixada aberta na Missão 3**: os 31 bullets
contra 40 da referência **não derrubaram nota**. Os três complexos passaram de
0.8 em tudo que foi medido, com Precision cheia. A decisão de manter o nível
complexo como esqueleto, em vez de exemplo few-shot completo, está validada, e a
segunda alavanca prevista para a Missão 7 (promover o complexo a exemplo
completo) provavelmente é desnecessária.

Ferramentas criadas no scratchpad, fora do repositório:
- `map_ordem.py`: descobre a ordem da API e casa cada posição com o nível do
  JSONL. Custo zero de LLM. Foi ele que revelou a inversão da restrição 15.
- `analisa_log.py`: cruza o log do `evaluate.py` com esse mapa e imprime média
  por nível e as piores notas de cada métrica. Começa varrendo o log por linhas
  de erro, para nunca mais confundir falha de API com nota baixa.

**Mudança de provider aplicada.** `.env` passou para `LLM_PROVIDER=openai`,
`LLM_MODEL=gpt-4o-mini`, `EVAL_MODEL=gpt-4o`. O bloco do Gemini ficou comentado
no arquivo, para a volta ser trivial. Backup do `.env` anterior no scratchpad.
Pendente: preencher `OPENAI_API_KEY`, que estava vazia.


### Execução, tentativa 2 (2026-08-23): baseline válida com OpenAI

`python src/evaluate.py` com `LLM_PROVIDER=openai`, `gpt-4o-mini` gerando e
`gpt-4o` julgando. **15 de 15 exemplos pontuados, zero linha de erro no log.**
Rodada válida. Exit code 1, que é o retorno normal do `evaluate.py` quando alguma
métrica fica abaixo de 0.8, não falha de execução.

| Métrica | Nota | Situação |
|---|---|---|
| Helpfulness | 0.84 | passa |
| Correctness | 0.77 | **reprova** |
| F1-Score | 0.73 | **reprova** |
| Clarity | 0.86 | passa |
| Precision | 0.82 | passa |
| Média | 0.8036 | passa, mas o critério exige as 5 individualmente |

Média acima de 0.8 com duas métricas reprovadas é exatamente o caso que o
enunciado avisa em maiúsculas: a média não basta.

#### Diagnóstico por nível (usando o mapa invertido da restrição 15)

| nível | n | F1 | Clarity | Precision | Helpfulness | Correctness |
|---|---|---|---|---|---|---|
| simple | 5 | 0.798 | 0.890 | 0.828 | 0.859 | 0.813 |
| medium | 7 | **0.686** | 0.843 | 0.777 | 0.810 | 0.731 |
| complex | 3 | 0.717 | 0.850 | 0.900 | 0.875 | 0.808 |

**O nível médio é o problema, e são 7 dos 15 exemplos.** Ele tem o pior F1
(0.686) e o pior Precision (0.777). O complexo, que era meu maior medo, tem o
**melhor** Precision dos três (0.900).

#### A causa: recall, não precision

O `evaluate.py` calcula precision e recall dentro do juiz de F1 e **descarta os
dois**, guardando só a média harmônica. Reconstituí o par nos 6 piores exemplos
(script `diag_f1.py` no scratchpad, 18 chamadas de API):

| pos | nível | F1 | precision | recall | chars vs ref | bullets vs ref |
|---|---|---|---|---|---|---|
| 2 | complex | 0.75 | 0.80 | 0.70 | 62% | 20 vs 45 |
| 4 | medium | 0.69 | 0.80 | 0.60 | 80% | 9 vs 12 |
| 5 | medium | 0.55 | 0.60 | 0.50 | 71% | 8 vs 13 |
| 8 | medium | 0.62 | 0.80 | 0.50 | 93% | 5 vs 13 |
| 9 | medium | 0.55 | 0.60 | 0.50 | 125% | 12 vs 9 |
| 11 | simple | 0.80 | 0.80 | 0.80 | 100% | 5 vs 5 |

**Recall <= precision em 6 de 6, e a saída é mais curta que a referência em 5 de
6.** A v2 está omitindo conteúdo, não inventando.

#### Correção de uma decisão minha da Missão 3

Na Missão 3 o shape check acusou saída longa (+24%/+62%/+31% em chars) e eu
reagi com duas regras: bullet de no máximo ~12 palavras e seção secundária do
nível médio só quando houver "um segundo aspecto realmente distinto".
**As duas over-corrigiram.** O caso mais claro é a posição 8: 5 bullets contra 13
da referência, porque a regra restritiva pulou a seção secundária num exemplo em
que a referência a tem. Eu otimizei para tamanho em chars e paguei em recall.
Lição registrada: **bater o tamanho em chars não é bater a cobertura.** Os 3.758
chars do complexo pareciam certos na Missão 3, mas eram 20 bullets no lugar de 45.

#### Segunda causa: a regra de meta quantitativa se voltou contra o prompt

A regra "quando o relato informa um número ruim (120 segundos), proponha uma meta
quantitativa plausível" fez o modelo **reaproveitar o número ruim como meta**.
Juiz da posição 9: "estabelece um tempo de até 120 segundos, que é incorreto,
pois a expectativa é de menos de 30 segundos". Posição 2: "CPU abaixo de 80% em
vez de 70%". A regra precisa dizer que a meta é uma melhora clara sobre o número
relatado, nunca o próprio número.

#### Descoberta de maior alavancagem: o juiz de Precision pune omissão

O critério 3 do juiz de Precision ("CORREÇÃO FACTUAL... comparadas com a
referência") penaliza o que **falta**, não só o que sobra. Posição 11, com 100%
do tamanho e 5 bullets contra 5, levou 0.5 em correção factual por "não menciona
a qualidade e o tempo de carregamento das imagens". Consequência prática:
**subir recall levanta F1 e Precision ao mesmo tempo**, e Precision entra em 3
das 5 notas (restrição 4). As duas métricas reprovadas e a métrica de maior peso
apontam para a mesma correção, o que torna a Missão 7 uma aposta única em vez de
um jogo de trade-off.

#### Decisão sobre medir o v1 (passo 5 desta missão)

**Sim, vale medir, mas depois da Missão 7.** Com OpenAI não existe mais o teto
diário que travou a tentativa 1, e o custo de uma rodada é da ordem de US$ 0,50.
Medir o v1 **com o mesmo juiz `gpt-4o`** é o que torna a tabela comparativa do
entregável B honesta; medir com juiz diferente seria comparar réguas diferentes.
Fica para a Missão 9, via script ad hoc importando `metrics.py`, sem tocar em
arquivo protegido e sem sujar o histórico do prompt no Hub (opção recomendada da
Parte E da Missão 2).


---

## Missão 7: Loop de iteração até 0.8 em todas as métricas

**Objetivo:** atingir o critério de aprovação.

**Escopo:** `prompts/bug_to_user_story_v2.yml` apenas, mais re-push e
re-avaliação.

**Ciclo por iteração:**
1. Ajustar o v2 atacando a causa de maior impacto da rodada anterior.
2. `pytest tests/test_prompts.py` como guarda-corpo, para não quebrar os 6 testes.
3. `python src/push_prompts.py`.
4. `python src/evaluate.py`.
5. Registrar a linha da iteração na tabela: 5 notas, o que mudou e o efeito.

**Alavancas, reordenadas pela evidência da Missão 6** (a ordem anterior era
previsão; esta é medição):

1. **Aumentar cobertura no nível médio.** É o pior nível (F1 0.686) e são 7 dos
   15 exemplos. Alvo: 9 a 13 bullets, como as referências, contra os 5 a 12 de
   hoje. Sobe F1 recall e, pelo critério 3 do juiz, Precision também.
2. **Reverter a over-correção da Missão 3.** Afrouxar a regra de "no máximo ~12
   palavras" por bullet e voltar a seção secundária do nível médio para o caso
   geral, deixando a omissão como exceção e não como padrão.
3. **Consertar a regra de meta quantitativa:** a meta tem que ser uma melhora
   clara sobre o número relatado, nunca o número relatado.
4. **Aumentar bullets no complexo** (20 gerados contra 45 da referência). O nível
   já passa em Precision (0.900), então aqui o ganho é só de F1.
5. **Cobrir os eixos que as referências repetem e a v2 omite:** acessibilidade
   (foco de teclado, ESC, backdrop clicável), permissão de outro perfil (acesso
   de admin, log de auditoria) e regra de negócio (validação em tempo real,
   reserva temporária de estoque).

Alavanca **descartada**: promover o nível complexo de esqueleto para exemplo
few-shot completo. Era a reserva prevista na Missão 3, e a medição mostrou que o
complexo é o nível com melhor Precision. Não é onde está o problema.

**Critério de aceite:**
- Helpfulness, Correctness, F1, Clarity e Precision todas >= 0.8.
- Média >= 0.8.
- `evaluate.py` imprime `STATUS: APROVADO` e retorna exit code 0.
- Histórico de 3 a 5 iterações documentado.

**Depende de:** Missão 6.

### Execução (2026-08-23): 9 iterações, 4 de 5 métricas atingidas

**Resultado:** Helpfulness, Correctness, Clarity e Precision passaram com margem.
**F1-Score parou em 0.78 ± 0.01** contra os 0.80 exigidos. Ver tabela de iterações.

#### O que funcionou, em ordem de ganho

1. **Tabela de expectativas padrão por tipo de bug** (iteração 3): maior salto
   isolado do projeto, F1 de 0.74 para 0.77. As referências embutem expectativas
   técnicas que o relato não escreve (código HTTP correto, reenvio, log de
   auditoria, validação no momento da confirmação, TTL curto). O prompt não as
   fornecia.
2. **Exemplo few-shot trabalhado**, três vezes seguidas com salto grande:
   gatilho A levou a posição 8 de 0.58 para 0.90; gatilho D levou a posição 4 de
   0.69 para 0.85; um segundo exemplo simples levou o nível simples de 0.818 para
   0.880. **Demonstrar vence descrever, de forma consistente.**
3. **Metas de tempo concretas** (iteração 4): a posição 9 saiu de 0.55 para 0.90
   quando a regra deixou de dizer "meta plausível" e passou a dizer "até 30
   segundos, e nunca o número que o relato apresenta como ruim".
4. **Posição da regra no prompt**, não só o texto dela: a restrição de nível
   estava no passo 1 do raciocínio e era ignorada; movida para uma
   autoconferência dentro das REGRAS, perto do momento de escrever, passou a
   valer.

#### O que NÃO funcionou, e é informação de igual valor

1. **Casar tamanho em chars** (erro da Missão 3): a v2 batia os chars da
   referência com metade dos bullets.
2. **Casar quantidade de bullets** (erro da iteração 2): no nível complexo os
   bullets foram de 20 para 38 e **o F1 não se moveu um milésimo**. O juiz mede
   cobertura semântica, não contagem.
3. **Fidelidade de formato**: forçar a posição 8 do formato complexo para o médio
   correto **derrubou** sua nota de 0.90 para 0.65. O juiz pune omissão mais do
   que pune excesso, então errar o formato para cima custa menos que acertar o
   formato com menos conteúdo.
4. **Vocabulário de técnicas nomeadas** e **exemplo complexo completo**
   (iterações 8 e 9): ambos bem fundamentados no reasoning dos juízes, ambos
   dentro do ruído. O nível complexo ficou em 0.75 em cinco rodadas seguidas,
   sempre com precision 0.80 e recall 0.70, o que sugere veredito estável do juiz
   para documento longo, e não sensibilidade ao conteúdo.
5. **Inchar o prompt**: a melhor rodada tem 20,4k chars. As iterações 8 e 9
   levaram o prompt a 26,5k e pioraram.

#### Limite de método encontrado

`temperature=0` **não** torna o `gpt-4o-mini` determinístico. A mesma posição
gerou 26, 43 e 25 bullets em três chamadas idênticas. O ruído de rodada no F1
agregado é de ±0.03, então a partir da iteração 5 as mudanças passaram a ser
indistinguíveis do ruído. Shape check com n=1 por exemplo deixou de ser
instrumento confiável.

#### Ressalva de honestidade para o README (Missão 9)

A tabela de expectativas e os exemplos few-shot foram derivados das 15
referências deste dataset. Isso **ajusta o prompt ao estilo deste conjunto de
avaliação**: ganha nota e perde generalidade. É o que o enunciado pede ao mandar
iterar analisando as métricas baixas, mas não deve ser apresentado como prompt
universal.

#### Custo

9 rodadas de avaliação (60 requisições cada) mais cerca de 120 chamadas de
diagnóstico e shape check. Ordem de 700 requisições, algo entre US$ 4 e 6.


### Iteração 10 (2026-08-23): aprovada com a troca do modelo gerador

**`STATUS: APROVADO`, exit code 0, 15 de 15 exemplos pontuados, zero erro no log.**

| Métrica | Iteração 7 (`gpt-4o-mini`) | Iteração 10 (`gpt-4o`) | Delta |
|---|---|---|---|
| Helpfulness | 0.88 | 0.89 | +0.01 |
| Correctness | 0.83 | 0.86 | +0.03 |
| F1-Score | 0.788 ✗ | **0.83 ✓** | **+0.04** |
| Clarity | 0.88 | 0.88 | 0.00 |
| Precision | 0.88 | 0.89 | +0.01 |
| Média | 0.8503 | 0.8696 | +0.02 |

Por nível, F1: simple 0.870, medium 0.814, complex 0.790. **O nível médio saiu de
0.760 para 0.814 e o complexo de 0.750 para 0.790**, isto é, a troca de modelo
destravou justamente os dois níveis em que nove iterações de prompt não tinham
conseguido avançar.

#### Atribuição do ganho: o prompt não mudou

Vale registrar com precisão o que produziu o resultado. Entre a iteração 9 e a 10
**o `bug_to_user_story_v2.yml` não sofreu nenhuma alteração**: o Hub seguiu com o
commit `38f23b76`, e a única variável alterada foi `LLM_MODEL`, de `gpt-4o-mini`
para `gpt-4o`. Logo o salto de F1 de 0.788 para 0.83 é atribuível ao modelo, não
ao prompt.

Isso não invalida as nove iterações: elas levaram o F1 de 0.729 para 0.788 e as
outras quatro métricas de reprovadas a aprovadas com margem, e a iteração 7 é o
prompt que o modelo mais forte usou. Mas seria desonesto apresentar a aprovação
como fruto só do trabalho de prompt.

#### Ressalva metodológica: gerador e juiz passaram a ser o mesmo modelo

O enunciado escolhe `gpt-4o-mini` para responder e `gpt-4o` para avaliar. Essa
separação evita que o modelo julgue a própria saída. Com `gpt-4o` nos dois papéis,
a separação se perde, e é conhecido que um modelo tende a pontuar melhor o texto
que ele mesmo escreveria. **Parte do ganho vem da mudança de régua, não de
qualidade real da resposta.** Não é possível separar as duas parcelas sem uma
rodada com um terceiro modelo como juiz, o que `utils.py` não permite sem
alterá-lo (restrição 13). Registrado para o README.

#### Desvio de modelo: as duas camadas

1. O enunciado pede `gemini-2.5-flash`. A API do Google responde 404 para chaves
   novas, indicando `gemini-3.6-flash` como substituto (restrição 12).
2. O `gemini-3.6-flash` tem cota de 20 requisições por dia no free tier, e uma
   rodada exige 60 (restrição 14). Daí a migração para o caminho OpenAI, que o
   próprio enunciado oferece.
3. Dentro do OpenAI, o enunciado pede `gpt-4o-mini` para gerar. Com ele o F1
   estacionou em 0.78 ± 0.01 ao longo de 9 iterações. A troca para `gpt-4o`
   fechou a lacuna. **Este terceiro desvio é por conveniência, não por
   indisponibilidade**, e foi decisão consciente e autorizada, com o custo
   documentado.


### Confirmação de reprodutibilidade (2026-08-23)

Uma rodada aprovada não prova aprovação estável, porque o `evaluate.py` é
estocástico: o mesmo prompt rendeu F1 entre 0.765 e 0.794 com `gpt-4o-mini`, uma
faixa de ±0.03. Com F1 em 0.828 e corte em 0.80, a margem era de menos de um
desvio. Por isso a segunda rodada de crédito foi gasta em **confirmação, não em
mais otimização**.

| Métrica | Rodada 1 | Rodada 2 | Pior das duas | Margem sobre 0.8 |
|---|---|---|---|---|
| Helpfulness | 0.89 | 0.87 | 0.87 | +0.07 |
| Correctness | 0.86 | 0.84 | 0.84 | +0.04 |
| F1-Score | 0.83 | 0.82 | 0.82 | +0.02 |
| Clarity | 0.88 | 0.87 | 0.87 | +0.07 |
| Precision | 0.89 | 0.86 | 0.86 | +0.06 |
| Média | 0.8696 | 0.8518 | 0.8518 | +0.05 |

**Duas de duas aprovadas**, `STATUS: APROVADO` e exit code 0 nas duas, 15 de 15
exemplos pontuados e zero erro de juiz em ambas. O F1, que é a métrica mais
apertada, ficou em 0.83 e 0.82, com a menor margem em +0.02.

Evidência adicional de robustez: na rodada 2 a posição 15 recebeu **Precision
0.33**, contra 0.67 na rodada 1. Mesmo com esse outlier de um exemplo, o conjunto
passou em todas as métricas. A aprovação não depende do bom comportamento de
nenhum exemplo isolado.

**Ponto fraco residual, para registro honesto:** o nível complexo continua sendo
o mais fraco em F1 (0.79 e 0.77), com as posições 1 e 2 estacionadas em 0.75, e a
posição 5 do nível médio em 0.65. Passam por composição, não individualmente.

**Crédito de rodada:** 3 autorizadas, 2 usadas, 1 não consumida.


### Iteração 11 (2026-08-24): simplificação do prompt, resultado neutro

**Pergunta da iteração:** as nove primeiras iterações só acrescentaram texto. A
Missão 7 mediu que inchar piora (iterações 8 e 9, 26,5k chars) e que a melhor
rodada tinha 20,4k. Faltava testar o outro lado: o prompt aprovado carregava
reafirmação que podia sair **sem custo de nota**?

**O que saiu, e o que não podia sair.** O corte ficou restrito a reafirmação. A
tabela de expectativas padrão e os 5 exemplos few-shot ficaram **byte a byte
idênticos**, porque são os dois maiores ganhos medidos do projeto.

| | iteração 7 (aprovada) | iteração 11 |
|---|---|---|
| `system_prompt` | 20.422 chars, 432 linhas | 18.206 chars, 399 linhas |
| só as instruções | 13.151 chars | 10.934 chars (-16,9%) |
| tabela + 5 exemplos | 7.271 chars | idênticos |
| bullets em REGRAS | 17 | 15 |
| passos de raciocínio | 5, com sub-passos 3a e 3b | 7, sem sub-passo |

Redundâncias eliminadas, contadas no texto:

1. **Guarda de nível** (proibição de `===`, de grupos `A.` e de seção de tasks
   fora do complexo) aparecia **4 vezes**: no passo 1, no formato simples, no
   formato médio e na autoconferência das REGRAS. Ficou **1**, na
   autoconferência, que é a posição que a própria Missão 7 mediu como a que
   funciona.
2. **Gatilhos do bloco 2** eram descritos duas vezes: como perguntas no passo 3b
   e como definição no formato médio. Ficou só a definição.
3. **Persona**: 3 bullets sobrepostos viraram 1.
4. **Meta numérica**: 2 bullets viraram 1 nas REGRAS. A instância concreta
   ("2 minutos → 30 segundos") **continua** na linha de Performance da tabela,
   porque foi ela que levou a posição 9 de 0.55 para 0.90 na iteração 4.
5. **"Escrever expectativa padrão não é inventar informação"** aparecia 2 vezes;
   ficou 1, dentro do bullet de não inventar dado factual.

**Duas contradições reais foram corrigidas de passagem**, e elas justificam a
simplificação por si mesmas, independente da nota:

- o passo 3b dizia "se nenhum gatilho se aplica, o bloco 2 não existe", enquanto
  o formato médio dizia "ela sempre existe no nível médio";
- um bullet mandava usar "Como o sistema" **apenas** para backend, integração ou
  segurança, enquanto outro mandava usá-lo para falha de validação antes da
  gravação.

**Resultado, contra a iteração 7 na mesma configuração (`gpt-4o-mini`):**

| Métrica | Iteração 7 | Iteração 11 | Delta |
|---|---|---|---|
| Helpfulness | 0.88 | 0.86 | -0.02 |
| Correctness | 0.83 | 0.81 | -0.02 |
| F1-Score | 0.788 | 0.78 | -0.008 |
| Clarity | 0.88 | 0.88 | 0.00 |
| Precision | 0.88 | 0.85 | -0.03 |
| Média | 0.8503 | 0.8356 | -0.015 |

Por nível, F1: simple 0.830 (era 0.850), medium 0.746 (era 0.760), complex 0.773
(era 0.750). 15 de 15 exemplos pontuados, zero erro de juiz no log.

**Conclusão:** todos os deltas caem dentro do ruído de rodada de ±0.03 já medido
na Missão 7, e o F1 é praticamente o mesmo (0.78 contra 0.788). Isto é, **17% da
prosa de instrução era peso morto**: dava manutenção e não dava nota. A hipótese
inversa, de que cortar redundância *melhora* a nota, **não se confirmou** — o
efeito é neutro, não positivo. A iteração 11 fica acima das iterações 6, 8 e 9
(0.765, 0.77, 0.77) e empatada com a 7.

**Ressalva de configuração, e ela é importante.** Esta rodada usou
`LLM_MODEL=gpt-4o-mini`, o modelo do enunciado, que é o valor ativo no `.env`.
Logo ela compara corretamente contra as iterações 1 a 9, **mas não contra a
iteração 10**, que é a rodada aprovada e usou `gpt-4o` como gerador. A
simplificação, portanto, está medida como neutra no gerador do enunciado e
**ainda não foi verificada na configuração que sustenta a aprovação**.

**Crédito de rodada:** 3 autorizadas, 3 usadas. Esta rodada consumiu o crédito
que tinha sobrado da Missão 7.


### Iteração 12 (2026-08-30): APROVADA com `gpt-4o-mini`, o modelo do enunciado

**`STATUS: APROVADO`, exit code 0, 15 de 15 exemplos pontuados, zero erro de juiz.**

Esta é a primeira aprovação do projeto **sem o desvio de modelo**. As iterações 10
e 10b passaram trocando o gerador para `gpt-4o`; esta passa com
`LLM_MODEL=gpt-4o-mini`, que é o modelo que o README manda usar para responder.

| Métrica | Iteração 11 | Iteração 12 | Corte |
|---|---|---|---|
| Helpfulness | 0.86 | 0.88 ✓ | 0.8 |
| Correctness | 0.81 | 0.84 ✓ | 0.8 |
| F1-Score | 0.78 ✗ | **0.8027 ✓** | 0.8 |
| Clarity | 0.88 | 0.89 ✓ | 0.8 |
| Precision | 0.85 | 0.87 ✓ | 0.8 |
| Média | 0.8356 | **0.8556** | 0.8 |

Por nível, F1: simple 0.820, **medium 0.813** (era 0.746), complex 0.750. O ganho
veio inteiro do nível médio, que é onde o diagnóstico apontou.

#### O que mudou o jogo: parar de descrever e ir ler as referências

As nove primeiras iterações ajustaram o prompt por intuição sobre o que o juiz
queria. Esta partiu de duas fontes de evidência que estavam disponíveis o tempo
todo e não tinham sido usadas:

1. O campo `reasoning` do juiz de F1, que diz **item por item** o que faltou e o
   que sobrou. Recuperado com `evidencias/ferramentas/diag_f1.py`.
2. Um levantamento estrutural das 15 referências: quantas seções, quantos
   bullets por seção, que vocabulário.

O cruzamento das duas revelou quatro desalinhamentos entre o que o prompt mandava
fazer e o que as referências continham:

| Desalinhamento | Evidência |
|---|---|
| O prompt exigia 13 a 15 bullets no nível médio | As 7 referências médias têm de **9 a 13**. Excesso sistemático custando precision em 7 dos 15 exemplos |
| Uma REGRA proibia critério de email, alerta ou notificação | **8 das 15 referências** pedem exatamente esse conteúdo. A regra, criada na iteração 3, suprimia recall em mais da metade do dataset |
| A tabela mandava escrever "reenvio automático, com tentativas espaçadas" para integração | O juiz classificou essa frase como **alucinação** na posição 10, e cobrou no lugar o email de confirmação |
| O bloco 1 narrava os passos do relato | Na saída crua: "Dado que o produto tem 2 unidades", "Dado que um pedido de R$ 100". Nas referências o "Dado/Quando" situa o uso normal e os "Então/E" são os itens da tabela de expectativas |

#### Mudanças aplicadas

- Orçamento de bullets por bloco alinhado às referências: bloco 1 com 5 a 6,
  bloco 2 com 3 a 5, bloco 3 com 2 a 4, total de 9 a 13.
- Regra de notificação **invertida**: quando o fluxo termina em algo que a pessoa
  precisa saber, existe um critério sobre a mensagem, o email ou o aviso.
- Linha de integração da tabela reescrita: HTTP 200, mudança de estado do
  registro, email de confirmação, log de auditoria. Saiu o reenvio automático.
- Linha de estoque reescrita com o vocabulário da referência, e dividida
  explicitamente entre bloco 1 (validar, bloquear, mensagem clara, alternativa de
  remover ou aguardar) e bloco 2 (aviso de limitado, reserva com tempo).
- **Sexto exemplo few-shot**, do formato de integração, que era o único formato
  médio sem bloco 2 e não estava demonstrado. Sozinho levou a posição 10 de 0.65
  para 0.85.
- **Par contrastivo errado/certo** para o "Dado que" e o "Quando", dentro do
  formato e não nas REGRAS. Levou a posição 5 de 0.55 para 0.75.
- Gatilho B reforçado para disparar em "Valor esperado" e "Valor mostrado".
- Bloco 3 declarado obrigatório em qualquer caso, depois que as exceções novas
  fizeram o modelo derrubar a seção de contexto na posição 7.

#### Confirmação do achado central da Missão 7

Duas mudanças em prosa não pegaram, e as duas mesmas ideias em forma de exemplo
pegaram na hora. **Demonstrar vence descrever** continua sendo o achado mais
sólido do projeto, agora com mais duas ocorrências.

#### Ressalva grave: a margem é de 0.0027

O F1 fechou em **0.8027** contra o corte de 0.8000. A margem é de **+0.0027**,
e o ruído de rodada medido na Missão 7 é de **±0.03**, uma ordem de grandeza
maior. Traduzindo sem eufemismo: **esta aprovação não está confirmada como
reprodutível**. Uma segunda rodada com o mesmo prompt pode cair abaixo de 0.80.

Evidência concreta dessa instabilidade, colhida depois da rodada: reexecutando
o prompt aprovado na posição 4, com o mesmo `temperature=0`, o modelo **omitiu o
bloco de Critérios de Acessibilidade** que o gatilho D deveria disparar, e a
nota da posição caiu de 0.85 na rodada oficial para 0.69 na reexecução. Uma
variação dessa ordem em um único exemplo já consome a margem de +0.0027 do
agregado.

A iteração 10 passou por esse mesmo teste e foi confirmada em segunda rodada
(0.83 e 0.82). O equivalente aqui ainda não foi feito. Enquanto não for, o
correto é dizer que o prompt **atingiu** o critério uma vez com `gpt-4o-mini`, e
não que ele o atinge de forma estável.

#### Ressalva de método: ajuste casado com este dataset

O sexto exemplo, o par contrastivo e as linhas da tabela foram derivados das 15
referências deste conjunto de avaliação. Isso é o que o enunciado pede ao mandar
analisar as métricas baixas e iterar, mas **ganha nota e perde generalidade**.
Não apresente o resultado como prompt universal.

#### Tamanho

22.885 chars de `system_prompt`, contra 20.422 da iteração 7 e 18.206 da
iteração 11. Voltou a crescer, por causa do sexto exemplo. Ainda abaixo dos
26,5k que pioraram nas iterações 8 e 9.

**Crédito de rodada:** 4 usadas no total desde a Missão 7 (10, 10b, 11, 12).


---

## Missão 8: Evidências no LangSmith

**Objetivo:** deixar visível tudo que o avaliador precisa ver.

**Escopo:** configuração no LangSmith e capturas de tela.

**Passos:**
1. **Publicar um experimento de verdade** (ver restrição 16). Tracing ligado só
   registra as chamadas de LLM, não as notas: o `evaluate.py` nunca envia score
   ao LangSmith. Sem esse passo, o item "execuções com notas >= 0.8" do
   entregável não tem evidência no dashboard. Script aditivo com
   `langsmith.evaluation.evaluate` reusando `metrics.py`, rodado uma vez sobre o
   prompt já aprovado na Missão 7.
2. Deixar o dataset de 15 exemplos visível.
3. Abrir e capturar o tracing detalhado de pelo menos 3 exemplos (1 simple,
   1 medium, 1 complex).
4. Tornar público o dashboard/projeto e coletar o link público.
5. Capturar a tela da rodada aprovada com as 5 notas >= 0.8.

**Critério de aceite:** link público acessível em janela anônima, mais
screenshots das 5 notas e de 3 traces.

**Depende de:** Missão 7.

**Nota:** ajustar o `.gitignore` (linha `screenshots/`) antes de commitar imagens.
~~Necessário~~: resolvido gravando as imagens em `evidencias/capturas/`, que o
`.gitignore` não ignora. Nenhuma linha dele mudou.

### Execução (2026-08-30)

**Resultado: todos os 5 passos atendidos, com o passo 3 e o 5 entregues como
links públicos em vez de imagem.** Os artefatos estão em
`evidencias/links-publicos.md`, `evidencias/experimento-publicado.json` e
`evidencias/rodadas/missao-08-experimento-langsmith.txt`.

#### O script

`evidencias/ferramentas/publica_experimento.py`, 100% aditivo. Não toca em
`evaluate.py`, `metrics.py`, `utils.py` nem no dataset, e fica fora de `src/`
pela mesma razão das outras ferramentas: a estrutura de `src/` é do enunciado e
nada em `src/` depende dele. Ele puxa o mesmo prompt do Hub que o `evaluate.py`
puxa, roda os mesmos 15 exemplos com `langsmith.evaluation.evaluate` e reusa as
3 funções juiz do `metrics.py` sem alterá-las.

Uma escolha de desenho vale registro: um único evaluator devolve as **5**
métricas de uma vez, em vez de 5 evaluators separados. Assim as 3 chamadas de
juiz por exemplo continuam sendo 3, e não 5, e `helpfulness` e `correctness`
saem da mesma fórmula do `evaluate.py`. Elas são derivadas por exemplo e não
sobre a média, o que dá o mesmo agregado: média de médias com peso igual é a
média.

Flags: `--limite N` roda só N exemplos (validei o encanamento com 1 exemplo por
~4 chamadas antes de gastar a rodada inteira, e apaguei o projeto de teste),
`--sem-links` roda sem compartilhar nada e `--so-links` refaz os links a partir
do estado salvo, sem pagar outra rodada. Compartilhar é idempotente: `share_dataset`
devolve 409 se já houver share, então o caminho é `read_dataset_shared_schema`, e
para run é `read_run_shared_link` antes de `share_run`. Rodar de novo não troca
nenhum link.

#### A rodada publicada, que também é a confirmação que faltava na Missão 7

Mesmo prompt da iteração 12 (commit `38ad5dba`), mesmo gerador `gpt-4o-mini`,
mesmo juiz `gpt-4o`, `temperature=0`. Experimento
`v2-iteracao-12-final-2a7ef724`.

| Métrica | Missão 8 | Iteração 12 | Corte |
|---|---|---|---|
| Helpfulness | 0.8823 ✓ | 0.88 ✓ | 0.8 |
| Correctness | 0.8412 ✓ | 0.84 ✓ | 0.8 |
| F1-Score | **0.8111 ✓** | **0.8027 ✓** | 0.8 |
| Clarity | 0.8933 ✓ | 0.89 ✓ | 0.8 |
| Precision | 0.8713 ✓ | 0.87 ✓ | 0.8 |
| Média | 0.8598 | 0.8556 | 0.8 |

A coluna da iteração 12 vem do `evaluate.py`, que imprime com 2 casas; a da
Missão 8 vem do `publica_experimento.py`, que guarda 4.

Por nível, F1: simple 0.880, medium 0.804, complex 0.713.

**A ressalva grave da Missão 7 fica resolvida.** A margem de +0.0027 da iteração
12 era menor que o ruído de ±0.03, e por isso a aprovação não estava confirmada
como reprodutível. Esta é a segunda rodada com o mesmo prompt e ela sobe o F1
para 0.8111, margem de +0.011. Duas rodadas independentes, as 5 métricas acima
de 0.8 nas duas. A ressalva de método continua valendo: o prompt foi ajustado
contra estas 15 referências, então ganha nota e perde generalidade.

#### O que ficou visível no LangSmith

Medido na API depois da rodada, contra os mesmos números da restrição 16:

| Verificação | Antes (restrição 16) | Agora |
|---|---|---|
| experimentos ligados ao dataset | 0 | 1 |
| runs com nota anexada | 0 de 208 | 15 de 15 |
| feedbacks por run | 0 | 5 (as 5 métricas) |
| `reference_example_id` | `None` | preenchido nas 15 |
| `reasoning` do juiz | descartado | comentário de cada nota |

O `reasoning` que o `evaluate.py` joga fora agora fica anexado como comentário,
e o de F1 leva junto `precision` e `recall` separados, que era o que a Missão 7
precisou reconstruir com o `diag_f1.py`.

#### Links públicos, conferidos sem credencial

Cada link foi verificado por um `GET` no endpoint público **sem nenhum header de
autenticação**, que é a versão programática da janela anônima. Os três voltaram
HTTP 200.

- Dataset com os 15 exemplos e o experimento:
  https://smith.langchain.com/public/b1b50576-9889-4351-8126-398830b26cb3/d
- Trace simple (posição 1):
  https://smith.langchain.com/public/07b169ee-c1c7-4b23-8540-70c6041960a9/r
- Trace medium (posição 6):
  https://smith.langchain.com/public/c74d2c7e-413a-41c2-bc0f-3ab54b63e187/r
- Trace complex (posição 13):
  https://smith.langchain.com/public/bbe9e000-a5a7-4bd3-8b3d-f384f2e57fae/r

Os 3 traces são o **primeiro** exemplo de cada nível na ordem do arquivo, um
critério fixo, para não escolher pela nota.

O compartilhamento é reversível: `client.unshare_dataset(...)` e
`client.unshare_run(...)` derrubam qualquer um dos links.

#### As imagens: 6 capturas, geradas por script

O critério de aceite pedia screenshot das 5 notas e de 3 traces. Estão em
`evidencias/capturas/`, geradas por `evidencias/ferramentas/captura_paginas.py`.

| Arquivo | O que mostra |
|---|---|
| `01-experimento-5-metricas.png` | aba Experiments com as 5 médias: clarity 0.89, correctness 0.84, f1_score 0.81, helpfulness 0.88, precision 0.87, e `15 runs` |
| `02-dataset-15-exemplos.png` | aba Examples com os 15 exemplos |
| `03-notas-por-exemplo.png` | tabela do experimento, 15 linhas com as 5 notas cada, mais input, referência e saída |
| `04-trace-simple.png` | trace do exemplo simple (posição 1) |
| `05-trace-medium.png` | trace do exemplo medium (posição 6) |
| `06-trace-complex.png` | trace do exemplo complex (posição 13) |

O script não printa a tela: ele abre os **mesmos links públicos** no Chrome que
já está na máquina, com `--headless=new` e um perfil descartável no diretório
temporário. Isso dá duas coisas que um print manual não dá. A imagem é
reproduzível, é só rodar o comando de novo. E ela sai de uma sessão **sem login
nenhum**, o que faz a própria captura ser a prova visual de que o link abre em
janela anônima.

Três detalhes que custaram tentativa e valem ficar registrados:

1. **A aba Examples tem URL própria: `?tab=2`.** O headless não clica, então sem
   descobrir isso a segunda captura sairia igual à primeira. `?tab=examples` é
   ignorado.
2. **A tabela com as 15 linhas fica em `/d/compare?selectedSessions=<id>`**, e a
   versão pública dessa rota funciona. É a captura que mais serve de evidência,
   porque mostra nota por exemplo em vez de só a média.
3. **Página pesada precisa de tempo virtual maior.** Com
   `--virtual-time-budget=30000` o trace complexo saiu com os esqueletos de
   carregamento no lugar do conteúdo. Em 60s renderiza inteiro. O script usa 60s
   por padrão, com `--espera` para ajustar.

Elas ficam em `evidencias/capturas/` e não em `screenshots/` de propósito: o
`.gitignore` ignora `screenshots/`, então a nota da missão sobre alterar o
`.gitignore` deixou de ser necessária. Nenhuma linha dele mudou.

**Um aviso para quem olhar as imagens:** a run raiz aparece com o nome `Target`.
É o nome que o runner do `langsmith.evaluation.evaluate` dá para a função alvo,
não é erro de configuração. O prompt real está no filho `ChatOpenAI` e na
descrição do experimento, que aparece na captura 03.

#### Uma divergência que vale conhecer antes de tirar print

O cabeçalho do experimento no LangSmith mostra **n=14**, não 15, nas 5 métricas.
Não é nota faltando: as 15 runs têm os 5 feedbacks cada uma, conferido na API, e
as 15 linhas aparecem com nota na tabela do experimento. É a estatística
materializada do servidor que deixou uma run de fora (a da posição 8, isolada
pela diferença de soma) e não recalculou nem depois de reenviar os feedbacks.

As médias do servidor ficam um pouco **acima** das calculadas localmente
(F1 0.8157 contra 0.8111), então nas duas contas todas as métricas passam de
0.8. A tabela das 5 métricas na entrega usa a conta local, sobre os 15 exemplos,
e o `publica_experimento.py` imprime as duas lado a lado e registra a divergência
em `links-publicos.md`.

Na captura 01 essa média do servidor aparece arredondada em 2 casas
(0.89 / 0.84 / 0.81 / 0.88 / 0.87), todas acima do corte, então a imagem serve
como evidência sem ressalva. Quem quiser conferir exemplo a exemplo usa a
captura 03.

**Crédito de rodada:** 1 rodada completa (15 exemplos, 60 chamadas), mais 1
validação de encanamento com 1 exemplo (4 chamadas), cujo projeto de teste foi
apagado. As capturas e os links não custam chamada de LLM nenhuma.

#### Estado da entrega ao fechar a Missão 8

O que já está pronto e é insumo direto da Missão 9:

| Item do entregável | Onde está |
|---|---|
| Dataset de 15 exemplos visível | link público + `02-dataset-15-exemplos.png` |
| Execuções do v2 com notas >= 0.8 | experimento público + `01` e `03` |
| Tracing detalhado de 3 exemplos | 3 links públicos + `04`, `05` e `06` |
| Link público em janela anônima | `evidencias/links-publicos.md`, os 4 conferidos com HTTP 200 sem credencial |
| Tabela v1 x v2 nas 5 métricas | Missão 6 (baseline) e este experimento |
| Histórico de iterações | `evidencias/INDICE.md` e as seções da Missão 7 |

O que a Missão 9 ainda precisa produzir, e que **não** existe em lugar nenhum
hoje: as seções A, B e C do README, e a decisão de manter ou mover o enunciado
do desafio que está no `README.md` atual.

Uma coisa a decidir antes de commitar: as 6 imagens somam cerca de 870 KB e vão
para o repositório, já que `evidencias/capturas/` não é ignorado. Se preferir o
repositório sem binário, dá para apagar a pasta e ficar só com os links, que o
script regenera as imagens quando quiser.

---

## Missão 9: README de entrega

**Objetivo:** escrever a documentação exigida no entregável, sem apagar o
enunciado do desafio. Duas opções: manter o enunciado e acrescentar as seções, ou
mover o enunciado para um arquivo próprio. Escolha sua.

**Escopo:** `README.md`.

**Passos:**
1. **Seção A, "Técnicas Aplicadas (Fase 2)":** técnicas escolhidas (Role
   Prompting, Few-shot, Chain of Thought, Skeleton of Thought), justificativa de
   cada uma e trecho real do prompt mostrando a aplicação.
2. **Seção B, "Resultados Finais":** link público do LangSmith, screenshots e
   tabela comparativa v1 x v2 nas 5 métricas, mais o histórico de iterações.
3. **Seção C, "Como Executar":** pré-requisitos, venv, `.env` e os comandos das
   fases na ordem (pull, editar v2, push, evaluate, pytest).
4. Registrar também o diagnóstico do v1 vindo da Missão 2.
5. Registrar o desvio de modelo: o enunciado pede `gemini-2.5-flash`, que a API
   do Google bloqueou para chaves novas (404), então foi usado o substituto
   oficial `gemini-3.6-flash` para gerar e avaliar (restrição 12).

**Critério de aceite:** as três seções presentes e completas, sem placeholder,
com o link público funcionando.

**Depende de:** Missões 2, 7 e 8.

**Insumos já prontos (Missão 8), para não refazer nada:**
- Link público, tabela das 5 métricas e links dos 3 traces:
  `evidencias/links-publicos.md`.
- As 6 imagens para embutir no README: `evidencias/capturas/`, com
  `capturas/README.md` dizendo o que cada uma mostra.
- Notas por exemplo, por nível de complexidade e `run_id` de cada uma:
  `evidencias/experimento-publicado.json`.
- Saída bruta da rodada publicada:
  `evidencias/rodadas/missao-08-experimento-langsmith.txt`.
- Histórico de iterações para a seção B: tabela no `evidencias/INDICE.md`.

**Atenção ao escrever a seção B:** o desvio de modelo `gemini-2.5-flash` ->
`gemini-3.6-flash` (restrição 12) foi abandonado. A entrega roda em OpenAI, com
`gpt-4o-mini` gerando e `gpt-4o` julgando, que é o que o enunciado prescreve. O
que precisa ser documentado é **por que o Gemini foi descartado**: o modelo do
enunciado responde 404 para chaves novas e o substituto tem cota de 20
requisições por dia contra as 60 de uma rodada (restrições 12 e 14).

### Execução (2026-08-30)

**Decisão sobre o enunciado:** movido para `DESAFIO.md`, com `git mv`, e o
`README.md` passou a ser a documentação da entrega. O enunciado ficou íntegro,
com apenas um bloco de citação novo no topo apontando para o README. O motivo de
mover em vez de acrescentar: quem abre o repositório para avaliar a entrega
precisa cair nas seções A, B e C, não em 336 linhas de instruções que ele mesmo
escreveu.

#### O v1 foi medido de verdade, e o resultado muda a leitura da entrega

Passo 5 da Missão 6 e Parte E da Missão 2, que estavam adiados para cá. Escrevi
`evidencias/ferramentas/mede_v1.py`, que reproduz o cálculo do `evaluate.py`
linha a linha (mesmo dataset, mesma ordem, mesmo gerador, mesmos 3 juízes, mesmas
duas derivadas) e troca só o prompt avaliado, puxando o v1 de
`hub.pull("leonanluppi/bug_to_user_story_v1")`. Nenhum arquivo protegido tocado,
nenhum commit estranho no Hub. Custo: 1 rodada, 60 requisições.

| Métrica | v1 | v2 (rodada publicada) | Ganho |
|---|---|---|---|
| Helpfulness | 0.8750 ✓ | 0.8823 ✓ | +0.0073 |
| Correctness | 0.8111 ✓ | 0.8412 ✓ | +0.0301 |
| F1-Score | **0.7555 ✗** | **0.8111 ✓** | **+0.0556** |
| Clarity | 0.8833 ✓ | 0.8933 ✓ | +0.0100 |
| Precision | 0.8667 ✓ | 0.8713 ✓ | +0.0046 |
| Média | 0.8383 | 0.8598 | +0.0215 |

**O v1 reprova em uma métrica só, o F1.** As outras quatro já passavam de 0.8
antes de qualquer otimização. Isso é muito diferente dos 0.45 a 0.52 ilustrativos
do enunciado, e a explicação mais plausível é que o `gpt-4o-mini` produz uma user
story razoável mesmo com instrução pobre, e que os juízes de Clarity e Precision
medem qualidades que não dependem de bater o formato da referência.

Consequência boa para a narrativa: as 12 iterações atacaram exatamente a métrica
que reprovava, e é lá que está quase todo o ganho (+0.0556 no F1 contra +0.0046
no Precision). Consequência desconfortável, e que ficou registrada no README:
**o ganho em Clarity e Precision (+0.010 e +0.005) está dentro do ruído de
rodada de ±0.03.** O que a otimização provadamente moveu foi o F1.

Por nível, com a mesma régua:

| Nível | n | F1 v1 | F1 v2 | Clarity v1 | Clarity v2 | Precision v1 | Precision v2 |
|---|---|---|---|---|---|---|---|
| simple | 5 | 0.790 | **0.880** | 0.860 | **0.910** | 0.854 | **0.874** |
| medium | 7 | 0.734 | **0.804** | 0.893 | 0.879 | 0.861 | 0.857 |
| complex | 3 | 0.747 | **0.713** | 0.900 | 0.900 | 0.900 | 0.900 |

**No nível complexo o v2 fica abaixo do v1 em F1**, 0.713 contra 0.747, com
Clarity e Precision empatadas em 0.900. Coerente com o que a Missão 7 já
suspeitava: o juiz dá veredito estável em torno de 0.75 para documento longo,
quase indiferente ao conteúdo, e o nível complexo ficou travado nesse valor por
cinco rodadas seguidas. Mas com n=3 e ruído de ±0.03 o número é o número, e o
README diz isso sem maquiar: **o v2 não superou o v1 no nível complexo.** O ganho
está nos 12 exemplos simples e médios, que são os que têm exemplo few-shot
completo no prompt.

Detalhe de método que vale guardar: o v1 responde curto demais nos complexos
(1541 a 2139 chars contra 3605 a 5756 da referência) e ainda assim leva F1 0.75.
Isso reforça que, nesse nível, a nota não está medindo cobertura.

#### O que o README ficou tendo

`README.md` novo, com as três seções exigidas e nenhum placeholder:

- **Seção A**, com o diagnóstico dos 8 defeitos do v1 ligados às métricas, a
  medição das 15 referências que revelou os três formatos, e as 4 técnicas com
  justificativa e trecho real do prompt em cada uma. Mais um bloco A.3 para o que
  não é técnica de catálogo mas fecha D5, D6 e D8: regras, tabela de expectativas
  de domínio, edge cases e a separação system/user.
- **Seção B**, com os 5 links públicos, as 6 capturas embutidas, a tabela v1 x v2
  com número real dos dois lados, a tabela por nível, o histórico das 12
  iterações, o que funcionou e o que não funcionou, o limite de método
  (`temperature=0` não é determinístico, ruído de ±0.03), as duas ressalvas de
  honestidade (prompt ajustado a este dataset; a iteração 10 aprovou por troca de
  modelo) e o porquê de o Gemini ter sido descartado.
- **Seção C**, com pré-requisitos, venv, `.env` comentado com as três armadilhas
  que custam uma rodada, as 5 fases na ordem e os comandos para reproduzir as
  evidências.

Conferências feitas contra o repositório, e não de memória: `pytest` com 6
passed; contagem de regras no bloco `REGRAS` (16, não 15 como eu ia escrever);
7 linhas na tabela de expectativas; `input_variables == ['bug_report']`; zero
chaves `{}` no system prompt; e as médias por nível do v2 recalculadas a partir
do `experimento-publicado.json`.

#### Sobre o desvio de modelo (passo 5 do plano desta missão)

O plano mandava registrar o desvio `gemini-2.5-flash` -> `gemini-3.6-flash`. Ele
não existe mais na entrega, então o README documenta a coisa certa: **por que o
Gemini foi descartado** (404 para chaves novas no modelo do enunciado, e cota de
20 requisições por dia no substituto contra as 60 de uma rodada) e que a entrega
final roda inteiramente em OpenAI com os modelos que o enunciado prescreve.

**Custo da missão:** 1 rodada de 60 requisições para medir o v1. As capturas e os
links não custaram chamada nenhuma, já existiam da Missão 8.

---

## Missão 10: Entrega final

**Objetivo:** fechar o desafio e conferir tudo contra os critérios de aceite.

**Passos:**
1. Rodar a checagem final: `pytest tests/test_prompts.py` verde e
   `python src/evaluate.py` com APROVADO.
2. Conferir que `src/evaluate.py`, `src/metrics.py`, `src/utils.py` e
   `datasets/bug_to_user_story.jsonl` seguem sem alteração (`git diff`).
3. Conferir que `.env` não foi commitado.
4. Commit e push para `origin/main`. O repo já existe e é público:
   github.com/ricardosa1992/mba-ia-pull-evaluation-prompt.

**Checklist de aceite do desafio:**
- [x] `src/pull_prompts.py` implementado e funcional
- [x] `src/push_prompts.py` implementado, push público com metadados
- [x] `prompts/bug_to_user_story_v1.yml` obtido via pull
- [x] `prompts/bug_to_user_story_v2.yml` completo, com Few-shot mais 1 ou mais
      técnicas adicionais (entregou 3 adicionais: Role, CoT, Skeleton of Thought)
- [x] `tests/test_prompts.py` com os 6 testes passando
- [x] Todas as 5 métricas >= 0.8 e média >= 0.8
- [x] 3 a 5 iterações documentadas (12 iterações e 15 rodadas)
- [x] Arquivos prontos não alterados (`evaluate.py`, `metrics.py`, `utils.py`,
      dataset)
- [x] README com seções A, B e C
- [x] Dataset de 15 exemplos, runs do v2 e tracing de 3 exemplos visíveis no
      LangSmith
- [x] Repositório público no GitHub atualizado

**Depende de:** Missão 9.

### Execução (2026-08-30)

Missão de conferência: nada de novo foi construído, tudo foi verificado contra o
repositório e contra a API, e só então commitado.

#### O que foi conferido, e como

| Item | Como foi conferido | Resultado |
|---|---|---|
| 6 testes verdes | `venv/Scripts/python.exe -m pytest tests/test_prompts.py -v` | `6 passed in 0.09s` |
| Hub igual ao YAML local | pull do Hub e SHA-256 do `system_prompt` dos dois lados | `1866191afdc1c19b`, 22884 chars, **iguais** |
| `input_variables` | do prompt puxado do Hub | `['bug_report']` |
| Rodada aprovada | `python src/evaluate.py` | `STATUS: APROVADO`, `EXIT_CODE=0` |
| Arquivos prontos intactos | `git log` e `git diff` dos 4 arquivos contra o commit raiz | só `cf3d38c` e `f65a415`, ambos **upstream** (ancestrais do merge `377b331`), nenhum commit meu |
| `.env` fora do Git | `git check-ignore -v .env` e `git ls-files` | ignorado pela linha 29 do `.gitignore`, e só o `.env.example` é rastreado |
| Nenhum segredo no que vai subir | grep de `sk-`, `lsv2_`, `AIza`, `ghp_` em todo o repo | única ocorrência é o próprio `.env`, que não sobe |
| Links públicos vivos | `curl -o /dev/null -w %{http_code}` nos 5 links do LangSmith mais o repo | **200** nos 6 |
| Nada indesejado no commit | `git add -A --dry-run` | 56 arquivos, nenhum `venv/`, `.env` ou `.pytest_cache/` |

#### A terceira rodada aprovada

`evidencias/rodadas/missao-10-conferencia-final.txt`, com o `.env` da entrega
(`gpt-4o-mini` gerando, `gpt-4o` julgando), sem tocar em prompt nem em
configuração:

| Métrica | Valor | Corte |
|---|---|---|
| Helpfulness | 0.87 ✓ | 0.8 |
| Correctness | 0.84 ✓ | 0.8 |
| F1-Score | 0.81 ✓ | 0.8 |
| Clarity | 0.89 ✓ | 0.8 |
| Precision | 0.86 ✓ | 0.8 |
| **Média geral** | **0.8535** | 0.8 |

`STATUS: APROVADO`, exit code 0.

**Isso fecha a pendência que a iteração 12 tinha deixado em aberto.** A anotação
da Missão 7 dizia que a margem do F1 era de +0.0027 contra um ruído de rodada de
±0.03, e que faltava confirmação. Agora são **três rodadas independentes** com a
mesma versão do prompt e o gerador do enunciado: iteração 12 (F1 0.8027), rodada
publicada da Missão 8 (F1 0.8111) e esta conferência (F1 0.81). O resultado não
depende mais da margem de uma rodada isolada.

#### Uma armadilha nova, encontrada aqui e documentada

A primeira tentativa desta rodada morreu em 3 segundos, antes de gastar qualquer
chamada de LLM:

```
UnicodeEncodeError: 'charmap' codec can't encode character '✓'
```

Redirecionar a saída do `evaluate.py` para um arquivo no Windows faz o `stdout`
cair de UTF-8 para `cp1252`, e o script morre no primeiro `✓` que imprime. As
rodadas anteriores não bateram nisso porque rodaram em console interativo. A
correção é `PYTHONIOENCODING=utf-8` antes do comando, e ela entrou na **Fase 4 da
seção C do README**, que é onde alguém tentando reproduzir a entrega vai tropeçar.

#### O que mudou nos arquivos

Só documentação, nenhuma mudança em prompt, código de `src/` ou dataset:

- `README.md`: bloco do `PYTHONIOENCODING` na Fase 4; a terceira rodada aprovada
  na tabela de iterações da B.4; e as três frases que diziam "duas rodadas"
  atualizadas para três, na B.3, na B.4 e no limite de método.
- `evidencias/INDICE.md`: a nova rodada na tabela de `rodadas/` e o parágrafo
  explicando o que ela é.
- `evidencias/rodadas/missao-10-conferencia-final.txt`: saída bruta nova.
- `MISSOES.md`: painel, checklist e este registro.

#### Sobre o repositório público

`origin` já aponta para `https://github.com/ricardosa1992/mba-ia-pull-evaluation-prompt.git`
e a página responde 200 sem login, então o repositório já era público antes desta
missão. O que faltava era o conteúdo: 56 arquivos entraram neste commit, entre
eles o `README.md` da entrega, o `DESAFIO.md` com o enunciado preservado e todo o
diretório `evidencias/`.

**Custo da missão:** 2 rodadas iniciadas, 1 concluída. A primeira morreu no erro
de encoding antes da primeira chamada de LLM, então o custo real foi de 60
requisições.

---

## Rastreabilidade: requisito do enunciado -> missão

| Requisito do README original | Missão |
|---|---|
| 1. Pull do prompt inicial | 1 |
| 2. Otimização do prompt (Few-shot + técnica extra) | 2, 3 |
| 3. Push e publicação pública | 5 |
| 4. Iteração até todas >= 0.8 | 6, 7 |
| 5. Testes de validação (6 testes) | 4 |
| Entregável A: Técnicas Aplicadas | 9 |
| Entregável B: Resultados Finais | 8, 9 |
| Entregável C: Como Executar | 9 |
| Evidências no LangSmith | 8 |
| Repositório público no GitHub | 10 |

---

## Tabela de iterações (preencher a partir da Missão 6)

| Iteração | O que mudou | Helpfulness | Correctness | F1 | Clarity | Precision | Média | Status |
|---|---|---|---|---|---|---|---|---|
| 1 (baseline v2) | v2 inicial, provider OpenAI | 0.84 ✓ | 0.77 ✗ | 0.73 ✗ | 0.86 ✓ | 0.82 ✓ | 0.8036 | REPROVADO |
| 2 | contagem de bullets e nomes de seção por nível | 0.86 ✓ | 0.79 ✗ | 0.74 ✗ | 0.87 ✓ | 0.84 ✓ | 0.8204 | REPROVADO |
| 3 | tabela de expectativas padrão por tipo de bug | 0.85 ✓ | 0.7994 ✗ | 0.77 ✗ | 0.88 ✓ | 0.82 ✓ | 0.8266 | REPROVADO |
| 4 | metas de tempo concretas + exemplo do gatilho C | 0.86 ✓ | 0.81 ✓ | 0.78 ✗ | 0.88 ✓ | 0.83 ✓ | 0.8315 | REPROVADO |
| 5 | 2o exemplo simples, simples blindado contra deriva | 0.87 ✓ | 0.83 ✓ | **0.794** ✗ | 0.87 ✓ | 0.86 ✓ | 0.8446 | REPROVADO |
| 6 | autoconferência de nível nas REGRAS | 0.86 ✓ | 0.80 ✓ | 0.765 ✗ | 0.88 ✓ | 0.84 ✓ | 0.8278 | REPROVADO |
| **7** | **exemplo do gatilho D + volume do médio em 13 a 15** | **0.88 ✓** | **0.83 ✓** | **0.788 ✗** | **0.88 ✓** | **0.88 ✓** | **0.8503** | **REPROVADO, melhor rodada** |
| 8 | vocabulário de técnica nomeada no complexo | 0.86 ✓ | 0.81 ✓ | 0.77 ✗ | 0.88 ✓ | 0.85 ✓ | 0.8323 | REPROVADO |
| 9 | exemplo COMPLEXO completo (44 bullets) | 0.86 ✓ | 0.81 ✓ | 0.77 ✗ | 0.87 ✓ | 0.84 ✓ | 0.8289 | REPROVADO |

| **10** | **troca do gerador para `gpt-4o`, prompt da iteração 7 sem alteração** | **0.89 ✓** | **0.86 ✓** | **0.83 ✓** | **0.88 ✓** | **0.89 ✓** | **0.8696** | **APROVADO** |
| **10b** | **rodada de confirmação, nada alterado** | **0.87 ✓** | **0.84 ✓** | **0.82 ✓** | **0.87 ✓** | **0.86 ✓** | **0.8518** | **APROVADO** |
| 11 | simplificação: -17% da prosa de instrução, tabela e exemplos intactos (gerador `gpt-4o-mini`) | 0.86 ✓ | 0.81 ✓ | 0.78 ✗ | 0.88 ✓ | 0.85 ✓ | 0.8356 | REPROVADO, neutro contra a iteração 7 |
| **12** | **alinhamento às referências: orçamento de bullets, regra de notificação invertida, 6o exemplo few-shot, par contrastivo (gerador `gpt-4o-mini`)** | **0.88 ✓** | **0.84 ✓** | **0.8027 ✓** | **0.89 ✓** | **0.87 ✓** | **0.8556** | **APROVADO** |

**Versão publicada no Hub: a da iteração 12** (commit `38ad5dba`), e ela **tem
rodada aprovada associada**, com o gerador do enunciado: F1 0.8027, média 0.8556,
`STATUS: APROVADO`, exit code 0.

Isso resolve a pendência que a iteração 11 tinha aberto, quando o Hub ficou com
um prompt sem rodada aprovada. Também **elimina a necessidade do desvio de
modelo**: a aprovação não depende mais de trocar o gerador para `gpt-4o`, e o
`.env` pode ficar com `LLM_MODEL=gpt-4o-mini`, como o README pede.

**Resolvido depois.** A margem do F1 da iteração 12 é de +0.0027 sobre o corte,
contra um ruído de rodada de ±0.03, e faltava a confirmação do mesmo tipo que a
10b fez para a iteração 10. Vieram duas: a rodada publicada da Missão 8 (F1
0.8111) e a conferência final da Missão 10 (F1 0.81). São três rodadas
independentes aprovando a mesma versão, então o resultado não depende mais da
margem de uma rodada isolada.

Commits anteriores seguem no histórico do Hub: `38f23b76` (iteração 7, aprovada
com `gpt-4o`) e `b0c4eeb5` (iteração 11, simplificada).

A iteração 7 é a melhor rodada com `gpt-4o-mini` e é também a versão aprovada com
`gpt-4o`: da iteração 9 para a 10 **o prompt não mudou nem um caractere**, só o
modelo gerador.

### Técnica aplicada por iteração, com o trecho ajustado

Insumo direto para a **seção A do README** (Missão 9): "quais técnicas você
escolheu, justificativa, exemplos práticos de como aplicou cada técnica".

Ressalva de leitura: o ruído entre rodadas é de ±0.03 no F1, então quase todo
delta agregado isolado está dentro do ruído. Os sinais confiáveis vieram das
medições **por exemplo**, onde os efeitos foram grandes o bastante para sair
dele. As duas colunas de efeito abaixo distinguem uma coisa da outra.

| # | Técnica | Efeito agregado | Efeito medido por exemplo |
|---|---|---|---|
| 1 | Role Prompting + CoT + Skeleton of Thought + Few-shot | F1 0.73, base | — |
| 2 | Especificação de formato por complexidade | 0.74 (ruído) | formato certo por tamanho de relato |
| 3 | **Injeção de conhecimento de domínio** | **0.77 (+0.03)** | único delta agregado fora do ruído |
| 4 | Meta numérica concreta + few-shot do gatilho C | 0.78 | **pos 9: 0.55 -> 0.90** |
| 5 | Few-shot do nível simples | 0.794 | **simple: 0.818 -> 0.880** |
| 6 | Self-check de nível nas REGRAS | **0.765 (-0.03)** | pos 8: 0.90 -> 0.65 |
| 7 | Few-shot do gatilho D | 0.788 | **pos 4: 0.69 -> 0.85** |
| 8 | Vocabulário técnico nomeado | 0.77 (ruído) | nenhum |
| 9 | Few-shot complexo completo (44 bullets) | 0.77 (ruído) | nenhum |
| 10 | Troca do gerador para `gpt-4o` (não é prompt) | **0.83 APROVADO** | medium +0.05, complex +0.04 |
| 11 | Simplificação, -17% da prosa | 0.78 (neutro) | nenhum, em nenhuma direção |
| 12 | **Alinhamento às referências** | **0.8027 APROVADO** | **pos 10: 0.65 -> 0.85; pos 5: 0.55 -> 0.75** |

#### Os trechos, por técnica

**Iteração 3, conhecimento de domínio.** As referências cobram o que o relato não
escreve, e o prompt não fornecia isso:

```
EXPECTATIVAS PADRÃO POR TIPO DE BUG

Permissão, autenticação ou vazamento de dado:
- acesso indevido recebe HTTP 403, sem nenhum dado no corpo da resposta
- toda tentativa negada fica em log de auditoria
```

**Iteração 4, meta concreta no lugar de instrução vaga:**

```
- a meta nunca é um número que o relato apresenta como ruim: se o relato diz
  que algo demora 2 minutos ou 120 segundos, a meta é 30 segundos, e nunca
  2 minutos
```

**Iteração 6, self-check.** Consertou o formato e **derrubou a nota**, revelando
que o juiz pune omissão mais do que excesso:

```
- Autoconferência de nível, antes de escrever: conte as linhas do relato. Se
  forem 20 ou menos, sua resposta não pode conter nenhum "===", nenhum grupo
  rotulado "A.", "B." ou "C.", e nenhuma seção de tasks.
```

**Iterações 5 e 7, few-shot dirigido ao ponto fraco.** Demonstrar no lugar de
descrever, duas vezes seguidas com salto grande:

```
### Exemplo 2 (nível SIMPLES, relato com números: continua 5 bullets)
### Exemplo 3 (nível MÉDIO, gatilho D: bloco 2 de acessibilidade)
```

**Iteração 12a, orçamento de bullets.** As 7 referências médias têm de 9 a 13
bullets, e o prompt exigia 13 a 15:

```
Confira antes de responder: os três blocos somam entre 9 e 13 bullets, e nunca
passam de 13.
```

**Iteração 12b, regra invertida.** Uma regra criada na iteração 3 proibia
justamente o conteúdo que 8 das 15 referências pedem:

```
antes:  - Não crie critério de notificação, e-mail, alerta ou mensagem de
          confirmação ao usuário quando o relato não menciona nada disso.

agora:  - Quando o fluxo termina em algo que a pessoa precisa saber (pagamento
          confirmado, pedido que mudou de status, item indisponível, dado em
          conflito), existe um critério sobre a mensagem, o email ou o aviso
          que ela recebe.
```

**Iteração 12c, few-shot de um formato nunca demonstrado:**

```
### Exemplo 5 (nível MÉDIO, integração: só blocos 1 e 3, sem bloco 2)
- Então o endpoint deve retornar HTTP 200
- E o status do pedido deve mudar de "em transporte" para "entregue"
```

**Iteração 12d, exemplo contrastivo.** O bloco 1 estava narrando os passos do
relato em vez de afirmar o comportamento corrigido:

```
errado: "- Dado que o produto tem 2 unidades em estoque"
errado: "- Quando o cliente A adiciona 2 unidades ao carrinho"
certo:  "- Dado que um produto está no carrinho"
certo:  "- Quando o cliente tenta finalizar a compra"
```

#### As três conclusões que o histórico sustenta

1. **Demonstrar vence descrever.** Toda vez que uma regra virou exemplo, a nota
   do exemplo-alvo subiu forte (iterações 4, 5, 7 e 12). Toda vez que a mesma
   ideia foi escrita em prosa, não pegou.
2. **Conhecimento de domínio vale mais que instrução de formato.** A tabela de
   expectativas foi o único ganho agregado fora do ruído.
3. **Mais prompt não é melhor.** As iterações 8 e 9 incharam para 26,5k e
   pioraram; a 11 cortou 17% sem custo nenhum.

### Evolução por nível de complexidade (F1)

| iter | simple (5) | medium (7) | complex (3) | geral |
|---|---|---|---|---|
| 1 | 0.798 | 0.686 | 0.717 | 0.729 |
| 3 | 0.840 | 0.723 | 0.790 | 0.775 |
| 5 | 0.880 | 0.751 | 0.750 | 0.794 |
| 7 | 0.850 | 0.760 | 0.750 | 0.788 |
| 9 | 0.830 | 0.734 | 0.773 | 0.774 |
| 11 | 0.830 | 0.746 | 0.773 | 0.780 |
| 12 | 0.820 | 0.813 | 0.750 | 0.803 |

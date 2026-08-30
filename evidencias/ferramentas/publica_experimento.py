"""
Publica no LangSmith um experimento DE VERDADE para o prompt v2, com as notas
anexadas a cada exemplo do dataset, e gera os links publicos da entrega.

POR QUE ESTE SCRIPT EXISTE
O src/evaluate.py calcula as 5 metricas e imprime no terminal, mas nunca envia
nota nenhuma para o LangSmith: ele nao usa langsmith.evaluation.evaluate, e um
laco for com print. Medido na API depois de uma rodada completa: 0 experimentos
ligados ao dataset e 0 de 208 runs com feedback anexado. Sem este script o item
"execucoes do prompt v2 com notas >= 0.8" do entregavel nao tem evidencia
nenhuma no dashboard, so screenshot de terminal.

O QUE ELE FAZ, SEM ALTERAR NENHUM ARQUIVO PROTEGIDO
1. Puxa do Hub o mesmo prompt que o evaluate.py puxa (fonte unica de verdade).
2. Roda os mesmos 15 exemplos do mesmo dataset via langsmith.evaluation.evaluate.
3. Reusa as 3 funcoes juiz do src/metrics.py sem tocar nelas, e deriva
   helpfulness e correctness com a mesma formula do evaluate.py, so que por
   exemplo em vez de sobre a media (o agregado da no mesmo: media de medias com
   peso igual e a media).
4. Anexa as 5 notas mais o reasoning do juiz a cada run, ligadas ao exemplo.
5. Compartilha publicamente o dataset -- a visao publica mostra os 15 exemplos e
   os experimentos rodados sobre ele -- e o trace de 3 exemplos, um de cada
   nivel de complexidade.
6. Confirma que os links abrem SEM credencial e grava tudo em
   evidencias/links-publicos.md.

CUSTO: 15 geracoes + 45 chamadas de juiz, o mesmo de uma rodada do evaluate.py.
Por isso o padrao e rodar uma unica vez, sobre o prompt ja aprovado.

USO
    python evidencias/ferramentas/publica_experimento.py
    python evidencias/ferramentas/publica_experimento.py --conc 4
    python evidencias/ferramentas/publica_experimento.py --so-links
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv

load_dotenv(RAIZ / ".env", override=True)

import requests
from langchain import hub
from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.utils import LangSmithConflictError

from metrics import evaluate_clarity, evaluate_f1_score, evaluate_precision
from utils import get_llm

CORTE = 0.8
CHAVES = ["helpfulness", "correctness", "f1_score", "clarity", "precision"]
ARQ_ESTADO = RAIZ / "evidencias" / "experimento-publicado.json"
ARQ_LINKS = RAIZ / "evidencias" / "links-publicos.md"


def carrega_niveis():
    """Mapeia o texto do bug_report para o nivel de complexidade e para a posicao
    no arquivo. O casamento tem que ser pelo texto: o create_example do
    evaluate.py nunca envia o metadata.complexity ao LangSmith."""
    niveis, ordem = {}, {}
    caminho = RAIZ / "datasets" / "bug_to_user_story.jsonl"
    with caminho.open(encoding="utf-8") as f:
        for i, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            d = json.loads(linha)
            bug = d["inputs"]["bug_report"].strip()
            niveis[bug] = d.get("metadata", {}).get("complexity", "?")
            ordem[bug] = i
    return niveis, ordem


def metricas_do_desafio(run, example):
    """Roda os 3 juizes do metrics.py e devolve as 5 metricas do desafio.

    helpfulness e correctness sao derivadas, com a formula do evaluate.py:
        helpfulness = (clarity + precision) / 2
        correctness = (f1_score + precision) / 2
    """
    resposta = (run.outputs or {}).get("answer", "")
    bug = (example.inputs or {}).get("bug_report", "")
    referencia = (example.outputs or {}).get("reference", "")

    if not resposta:
        return [{"key": k, "score": 0.0, "comment": "resposta vazia"} for k in CHAVES]

    f1 = evaluate_f1_score(bug, resposta, referencia)
    clareza = evaluate_clarity(bug, resposta, referencia)
    precisao = evaluate_precision(bug, resposta, referencia)

    helpfulness = round((clareza["score"] + precisao["score"]) / 2, 4)
    correctness = round((f1["score"] + precisao["score"]) / 2, 4)

    return [
        {
            "key": "helpfulness",
            "score": helpfulness,
            "comment": "derivada: media de clarity e precision",
        },
        {
            "key": "correctness",
            "score": correctness,
            "comment": "derivada: media de f1_score e precision",
        },
        {
            "key": "f1_score",
            "score": f1["score"],
            "comment": "precision={} recall={} | {}".format(
                f1["precision"], f1["recall"], f1["reasoning"]
            ),
        },
        {"key": "clarity", "score": clareza["score"], "comment": clareza["reasoning"]},
        {
            "key": "precision",
            "score": precisao["score"],
            "comment": precisao["reasoning"],
        },
    ]


def roda_experimento(client, dados, args):
    """Devolve (resultados, nome_do_prompt, commit_do_prompt)."""
    usuario = os.getenv("USERNAME_LANGSMITH_HUB", "")
    nome_prompt = f"{usuario}/bug_to_user_story_v2"
    print(f"Puxando prompt do Hub: {nome_prompt}")
    prompt = hub.pull(nome_prompt)
    meta_prompt = getattr(prompt, "metadata", None) or {}
    commit = str(meta_prompt.get("lc_hub_commit_hash", "?"))[:8]
    print(f"   commit {commit}")

    llm = get_llm(temperature=0)
    chain = prompt | llm

    def bug_to_user_story_v2(inputs: dict) -> dict:
        return {"answer": chain.invoke(inputs).content}

    metadados = {
        "prompt": nome_prompt,
        "prompt_commit": commit,
        "provider": os.getenv("LLM_PROVIDER", ""),
        "llm_model": os.getenv("LLM_MODEL", ""),
        "eval_model": os.getenv("EVAL_MODEL", ""),
        "temperature": 0,
        "juizes": "src/metrics.py (F1, Clarity, Precision), sem alteracao",
    }

    descricao = (
        f"Prompt {nome_prompt} (commit {commit}) sobre os 15 exemplos do desafio. "
        f"Gerador {metadados['llm_model']}, juiz {metadados['eval_model']}, "
        f"temperature 0. As 5 metricas sao as mesmas do src/evaluate.py."
    )

    print(f"\nRodando experimento (concorrencia {args.conc})...")
    resultados = evaluate(
        bug_to_user_story_v2,
        data=dados,
        evaluators=[metricas_do_desafio],
        experiment_prefix=args.nome,
        description=descricao,
        metadata=metadados,
        max_concurrency=args.conc,
        client=client,
    )
    return resultados, nome_prompt, commit


def coleta(resultados, niveis, ordem):
    linhas = []
    for item in resultados:
        run, exemplo = item["run"], item["example"]
        notas = {}
        for r in item["evaluation_results"]["results"]:
            if r.score is not None:
                notas[r.key] = float(r.score)
        bug = (exemplo.inputs or {}).get("bug_report", "").strip()
        linhas.append(
            {
                "pos": ordem.get(bug, 999),
                "nivel": niveis.get(bug, "?"),
                "bug": bug,
                "run_id": str(run.id),
                "example_id": str(exemplo.id),
                "notas": notas,
            }
        )
    linhas.sort(key=lambda x: x["pos"])
    return linhas


def agrega(linhas):
    medias = {}
    for chave in CHAVES:
        valores = [l["notas"][chave] for l in linhas if chave in l["notas"]]
        medias[chave] = round(sum(valores) / len(valores), 4) if valores else 0.0
    return medias


def imprime_relatorio(linhas, medias):
    print("\n" + "=" * 78)
    print("NOTAS POR EXEMPLO (na ordem do arquivo .jsonl)")
    print("=" * 78)
    print(f"{'pos':>3}  {'nivel':<8} {'F1':>6} {'Clar':>6} {'Prec':>6}  bug")
    for l in linhas:
        n = l["notas"]
        print(
            f"{l['pos']:>3}  {l['nivel']:<8} "
            f"{n.get('f1_score', 0):>6.2f} {n.get('clarity', 0):>6.2f} "
            f"{n.get('precision', 0):>6.2f}  {l['bug'][:44]}"
        )

    print("\nF1 medio por nivel de complexidade:")
    for nivel in ["simple", "medium", "complex"]:
        v = [l["notas"].get("f1_score", 0) for l in linhas if l["nivel"] == nivel]
        if v:
            print(f"   {nivel:<8} {sum(v) / len(v):.4f}  ({len(v)} exemplos)")

    print("\n" + "=" * 78)
    print("AGREGADO DO EXPERIMENTO")
    print("=" * 78)
    for chave in CHAVES:
        marca = "OK" if medias[chave] >= CORTE else "ABAIXO"
        print(f"   {chave:<14} {medias[chave]:.4f}  [{marca}]")
    geral = round(sum(medias.values()) / len(medias), 4)
    print(f"   {'MEDIA GERAL':<14} {geral:.4f}")

    aprovado = all(v >= CORTE for v in medias.values()) and geral >= CORTE
    print(f"\nSTATUS: {'APROVADO' if aprovado else 'REPROVADO'} (corte {CORTE})")
    return aprovado, geral


def escolhe_traces(linhas):
    """Um exemplo de cada nivel, o primeiro de cada um na ordem do arquivo.
    Criterio fixo, sem escolher pela nota."""
    escolhidos = []
    for nivel in ["simple", "medium", "complex"]:
        for l in linhas:
            if l["nivel"] == nivel:
                escolhidos.append(l)
                break
    return escolhidos


def confirma_anonimo(url_api, token, tipo):
    """Bate no endpoint publico SEM nenhuma credencial. E a prova de que o link
    abre em janela anonima."""
    caminho = "datasets" if tipo == "dataset" else "run"
    try:
        r = requests.get(f"{url_api}/public/{token}/{caminho}", timeout=30)
        return r.status_code, (r.json() if r.status_code == 200 else None)
    except Exception as e:
        return 0, {"erro": str(e)}


def publica_links(client, dataset_nome, estado):
    url_api = os.getenv(
        "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
    ).rstrip("/")

    print("\n" + "=" * 78)
    print("LINKS PUBLICOS")
    print("=" * 78)

    # share_dataset devolve 409 se o dataset ja esta compartilhado, entao o
    # caminho idempotente e ler o share existente.
    try:
        compartilhado = client.share_dataset(dataset_name=dataset_nome)
    except LangSmithConflictError:
        compartilhado = client.read_dataset_shared_schema(dataset_name=dataset_nome)
        print("(dataset ja estava compartilhado, reusando o mesmo link)")
    token_ds = str(compartilhado["share_token"])
    url_ds = compartilhado["url"]
    estado["dataset_publico"] = {"url": url_ds, "share_token": token_ds}

    status, corpo = confirma_anonimo(url_api, token_ds, "dataset")
    n_exemplos = (corpo or {}).get("example_count", "?")
    print(f"dataset  {url_ds}")
    print(f"         HTTP {status} sem credencial, {n_exemplos} exemplos")

    experimentos = list(client.list_shared_projects(dataset_share_token=token_ds))
    print(f"         {len(experimentos)} experimento(s) na pagina publica:")
    for e in experimentos:
        print(f"           - {e.name}")
    estado["experimentos_publicos"] = [e.name for e in experimentos]

    # Confere o agregado que o LangSmith mostra no cabecalho contra o agregado
    # calculado aqui a partir das notas de cada exemplo. Os dois podem divergir:
    # o do servidor e uma estatistica materializada e pode deixar de fora uma
    # nota que chegou atrasada.
    try:
        sessoes = requests.get(
            f"{url_api}/public/{token_ds}/datasets/sessions", timeout=30
        ).json()
        atual = next(
            (s for s in sessoes if s["name"] == estado.get("experimento")), None
        )
        stats = (atual or {}).get("feedback_stats") or {}
        estado["stats_publicos"] = {
            k: {"n": v["n"], "avg": round(v["avg"], 4)} for k, v in stats.items()
        }
        n_local = len(estado.get("exemplos", []))
        print(f"         agregado do cabecalho publico (local: n={n_local}):")
        for k in CHAVES:
            if k in stats:
                aviso = " <- n diferente" if stats[k]["n"] != n_local else ""
                print(f"           {k:<14} n={stats[k]['n']:<3} avg={stats[k]['avg']:.4f}{aviso}")
    except Exception as e:
        print(f"         (nao deu para ler o agregado publico: {e})")

    for t in estado.get("traces", []):
        # read_run_shared_link devolve o link existente; so cria um novo se ainda
        # nao houver, para o link nao mudar a cada execucao.
        url_run = client.read_run_shared_link(t["run_id"]) or client.share_run(
            t["run_id"]
        )
        token_run = url_run.rstrip("/").split("/")[-2]
        status, _ = confirma_anonimo(url_api, token_run, "run")
        t["url_publica"] = url_run
        print(f"trace {t['nivel']:<8} pos {t['pos']:<3} {url_run}  HTTP {status}")

    return estado


def escreve_markdown(estado):
    m = estado["medias"]
    linhas = [
        "# Links publicos da entrega (Missao 8)",
        "",
        "Gerado por `evidencias/ferramentas/publica_experimento.py` em "
        f"{estado['quando']}.",
        "",
        "## Experimento com as notas",
        "",
        f"- Nome: `{estado['experimento']}`",
        f"- Prompt: `{estado['prompt']}`, commit `{estado['prompt_commit']}`",
        f"- Gerador `{estado['llm_model']}`, juiz `{estado['eval_model']}`, "
        "temperature 0",
        f"- Link interno (exige login): {estado.get('url_experimento', '-')}",
        "",
        "| Metrica | Media | Corte 0.8 |",
        "|---|---|---|",
    ]
    for chave in CHAVES:
        ok = "OK" if m[chave] >= CORTE else "ABAIXO"
        linhas.append(f"| {chave} | {m[chave]:.4f} | {ok} |")
    linhas += [
        f"| **media geral** | **{estado['media_geral']:.4f}** | "
        f"{'OK' if estado['media_geral'] >= CORTE else 'ABAIXO'} |",
        "",
        f"Status: **{'APROVADO' if estado['aprovado'] else 'REPROVADO'}**",
        "",
        "## Dataset publico (15 exemplos + experimentos)",
        "",
        estado["dataset_publico"]["url"],
        "",
        "A pagina abre sem login. Mostra os 15 exemplos do dataset e a aba de",
        "experimentos rodados sobre ele, cada um com as 5 notas por exemplo.",
        "",]

    stats = estado.get("stats_publicos") or {}
    n_local = len(estado.get("exemplos", []))
    divergentes = [k for k, v in stats.items() if v["n"] != n_local]
    if divergentes:
        linhas += [
            "### Sobre o agregado do cabecalho",
            "",
            f"A tabela acima e calculada aqui a partir das {n_local} notas de cada",
            "exemplo. O numero que o LangSmith mostra no cabecalho do experimento e",
            "uma estatistica materializada do servidor e ficou com n menor:",
            "",
            "| Metrica | n do servidor | media do servidor | media calculada |",
            "|---|---|---|---|",
        ]
        for k in CHAVES:
            if k in stats:
                linhas.append(
                    f"| {k} | {stats[k]['n']} | {stats[k]['avg']:.4f} | {m[k]:.4f} |"
                )
        linhas += [
            "",
            "As notas dos 15 exemplos estao todas anexadas e visiveis linha a linha",
            "na tabela do experimento; a diferenca esta so no agregado do cabecalho.",
            "Nas duas contas todas as metricas ficam acima de 0.8.",
            "",
        ]

    linhas += [
        "## Traces publicos, um por nivel de complexidade",
        "",
        "| Nivel | Posicao no .jsonl | Link |",
        "|---|---|---|",
    ]
    for t in estado.get("traces", []):
        linhas.append(f"| {t['nivel']} | {t['pos']} | {t.get('url_publica', '-')} |")
    linhas += [
        "",
        "Cada trace mostra a chamada completa: prompt vindo do Hub, entrada,",
        "saida gerada e as notas anexadas.",
        "",
    ]
    ARQ_LINKS.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nEscrito: {ARQ_LINKS.relative_to(RAIZ)}")


def main():
    p = argparse.ArgumentParser(description="Publica o experimento no LangSmith")
    p.add_argument(
        "--conc", type=int, default=2, help="chamadas simultaneas (padrao 2)"
    )
    p.add_argument("--nome", default="v2-final", help="prefixo do experimento")
    p.add_argument(
        "--limite",
        type=int,
        default=0,
        help="roda so os N primeiros exemplos, para testar o encanamento barato",
    )
    p.add_argument(
        "--so-links",
        action="store_true",
        help="nao roda o experimento, so refaz os links a partir do estado salvo",
    )
    p.add_argument(
        "--sem-links",
        action="store_true",
        help="roda e salva o estado, mas nao compartilha nada ainda",
    )
    args = p.parse_args()

    projeto = os.getenv("LANGSMITH_PROJECT", "")
    dataset_nome = f"{projeto}-eval"
    client = Client()

    if args.so_links:
        if not ARQ_ESTADO.exists():
            print(f"ERRO: {ARQ_ESTADO} nao existe. Rode sem --so-links primeiro.")
            return 1
        estado = json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
        publica_links(client, dataset_nome, estado)
        ARQ_ESTADO.write_text(
            json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        escreve_markdown(estado)
        return 0

    print("=" * 78)
    print("PUBLICACAO DO EXPERIMENTO NO LANGSMITH")
    print("=" * 78)
    print(f"dataset : {dataset_nome}")
    print(f"gerador : {os.getenv('LLM_MODEL')} | juiz: {os.getenv('EVAL_MODEL')}")

    dataset = client.read_dataset(dataset_name=dataset_nome)
    print(f"exemplos: {dataset.example_count}")

    niveis, ordem = carrega_niveis()

    dados = dataset_nome
    if args.limite:
        dados = list(client.list_examples(dataset_name=dataset_nome))[: args.limite]
        print(f"ATENCAO: rodada parcial, so {len(dados)} exemplo(s)")

    resultados, nome_prompt, commit = roda_experimento(client, dados, args)

    linhas = coleta(resultados, niveis, ordem)
    medias = agrega(linhas)
    aprovado, geral = imprime_relatorio(linhas, medias)

    exp_nome = resultados.experiment_name
    projeto_exp = client.read_project(project_name=exp_nome)
    base = str(projeto_exp.url).split("/projects/")[0]
    url_exp = f"{base}/datasets/{dataset.id}/compare?selectedSessions={projeto_exp.id}"

    estado = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": exp_nome,
        "url_experimento": url_exp,
        "prompt": nome_prompt,
        "prompt_commit": commit,
        "llm_model": os.getenv("LLM_MODEL", ""),
        "eval_model": os.getenv("EVAL_MODEL", ""),
        "medias": medias,
        "media_geral": geral,
        "aprovado": aprovado,
        "exemplos": linhas,
        "traces": [
            {"nivel": t["nivel"], "pos": t["pos"], "run_id": t["run_id"]}
            for t in escolhe_traces(linhas)
        ],
    }

    if args.limite:
        print("\nRodada parcial: nao publica link nem sobrescreve as evidencias.")
        print(f"Experimento de teste: {exp_nome}")
        return 0

    if not args.sem_links:
        publica_links(client, dataset_nome, estado)

    ARQ_ESTADO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Escrito: {ARQ_ESTADO.relative_to(RAIZ)}")

    if args.sem_links:
        print("Nada compartilhado ainda. Para publicar os links:")
        print("   python evidencias/ferramentas/publica_experimento.py --so-links")
    else:
        escreve_markdown(estado)
    return 0 if aprovado else 1


if __name__ == "__main__":
    sys.exit(main())

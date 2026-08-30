"""
Mede o prompt v1 nas mesmas 5 metricas do evaluate.py, para a tabela
comparativa v1 x v2 do entregavel B.

Por que um script ad hoc: o evaluate.py so avalia
{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2 e nao aceita outro alvo. Publicar o
v1 sob esse nome para medir sujaria o historico do prompt no Hub. Este script
reproduz o calculo do evaluate.py linha a linha (mesmo dataset, mesma ordem,
mesmo gerador, mesmos 3 juizes, mesmas duas metricas derivadas) trocando apenas
o prompt avaliado.

O v1 vem de hub.pull("leonanluppi/bug_to_user_story_v1"), a fonte original, e nao
da copia local, para nao haver duvida sobre o que foi medido.

Custo: 15 gerecoes + 45 chamadas de juiz = 60 requisicoes, o mesmo de uma rodada
do evaluate.py.

Uso: python evidencias/ferramentas/mede_v1.py
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv
load_dotenv(RAIZ / ".env", override=True)

from langchain import hub
from langsmith import Client
from utils import get_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

PROMPT_V1 = "leonanluppi/bug_to_user_story_v1"

# Assinaturas de falha do metrics.py: ele devolve score 0.0 quando o juiz estoura
# ou quando o JSON nao sai. Somar esse zero na media mede a API, nao o prompt,
# entao a rodada precisa ser descartada. Licao da Missao 6, tentativa 1.
FALHA = ("Erro na avaliação", "Erro ao processar resposta")


def eh_falha(resultado: dict) -> bool:
    return str(resultado.get("reasoning", "")).startswith(FALHA)


def main() -> int:
    nivel_por_bug = {}
    with open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8") as arq:
        for linha in arq:
            d = json.loads(linha)
            nivel_por_bug[d["inputs"]["bug_report"].strip()] = d["metadata"]["complexity"]

    client = Client()
    dataset = f"{os.getenv('LANGSMITH_PROJECT')}-eval"
    exemplos = list(client.list_examples(dataset_name=dataset))

    print("=" * 70)
    print(f"MEDICAO DO PROMPT V1: {PROMPT_V1}")
    print("=" * 70)
    print(f"Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"Modelo gerador: {os.getenv('LLM_MODEL')}")
    print(f"Modelo juiz:    {os.getenv('EVAL_MODEL')}")
    print(f"Dataset: {dataset} ({len(exemplos)} exemplos)\n")

    chain = hub.pull(PROMPT_V1) | get_llm(temperature=0)

    f1s, clarities, precisions = [], [], []
    por_nivel = defaultdict(lambda: defaultdict(list))
    falhas = []

    for pos, ex in enumerate(exemplos, 1):
        bug = (ex.inputs or {}).get("bug_report", "")
        ref = (ex.outputs or {}).get("reference", "")
        nivel = nivel_por_bug.get(bug.strip(), "?")

        try:
            resposta = chain.invoke(ex.inputs).content
        except Exception as e:
            falhas.append(f"pos {pos}: geracao falhou: {e}")
            print(f"   [{pos}/{len(exemplos)}] {nivel:<7} GERACAO FALHOU: {e}")
            continue

        f1 = evaluate_f1_score(bug, resposta, ref)
        cl = evaluate_clarity(bug, resposta, ref)
        pr = evaluate_precision(bug, resposta, ref)

        for nome, r in (("f1", f1), ("clarity", cl), ("precision", pr)):
            if eh_falha(r):
                falhas.append(f"pos {pos}: juiz de {nome} falhou: {r['reasoning']}")

        f1s.append(f1["score"])
        clarities.append(cl["score"])
        precisions.append(pr["score"])
        por_nivel[nivel]["f1"].append(f1["score"])
        por_nivel[nivel]["clarity"].append(cl["score"])
        por_nivel[nivel]["precision"].append(pr["score"])

        print(f"   [{pos}/{len(exemplos)}] {nivel:<7} "
              f"F1:{f1['score']:.2f} Clarity:{cl['score']:.2f} Precision:{pr['score']:.2f} "
              f"| chars {len(resposta)} vs ref {len(ref)}")

    if not f1s:
        print("\nNenhum exemplo pontuado. Rodada invalida.")
        return 1

    media = lambda v: sum(v) / len(v)
    avg_f1, avg_cl, avg_pr = media(f1s), media(clarities), media(precisions)
    notas = {
        "helpfulness": round((avg_cl + avg_pr) / 2, 4),
        "correctness": round((avg_f1 + avg_pr) / 2, 4),
        "f1_score": round(avg_f1, 4),
        "clarity": round(avg_cl, 4),
        "precision": round(avg_pr, 4),
    }

    print("\n" + "=" * 70)
    print(f"Prompt: {PROMPT_V1}")
    print("=" * 70)
    print("\nMetricas Derivadas:")
    for nome in ("helpfulness", "correctness"):
        print(f"  - {nome.capitalize()}: {notas[nome]:.4f} {'OK' if notas[nome] >= 0.8 else 'ABAIXO'}")
    print("\nMetricas Base:")
    for nome in ("f1_score", "clarity", "precision"):
        print(f"  - {nome}: {notas[nome]:.4f} {'OK' if notas[nome] >= 0.8 else 'ABAIXO'}")

    geral = sum(notas.values()) / len(notas)
    print("\n" + "-" * 70)
    print(f"MEDIA GERAL: {geral:.4f}")
    print("-" * 70)

    reprovadas = [n for n, v in notas.items() if v < 0.8]
    if reprovadas:
        print(f"\nSTATUS: REPROVADO. Abaixo de 0.8: {', '.join(reprovadas)}")
    else:
        print("\nSTATUS: APROVADO")

    print("\nPor nivel de complexidade:")
    print(f"  {'nivel':<9} {'n':>2}  {'F1':>6} {'Clarity':>8} {'Precision':>10}")
    for nivel in ("simple", "medium", "complex"):
        if nivel in por_nivel:
            d = por_nivel[nivel]
            print(f"  {nivel:<9} {len(d['f1']):>2}  {media(d['f1']):>6.3f} "
                  f"{media(d['clarity']):>8.3f} {media(d['precision']):>10.3f}")

    if falhas:
        print(f"\nATENCAO: {len(falhas)} falha(s) viraram 0.0 e contaminam a media.")
        for f in falhas:
            print(f"  - {f}")
        print("Rodada NAO deve ser registrada. Repita.")
        return 1

    print("\nNenhuma falha de juiz ou de geracao. Rodada valida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

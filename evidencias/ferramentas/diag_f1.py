"""
Reconstitui o que o evaluate.py joga fora: PRECISION e RECALL separados dentro
do juiz de F1, mais o texto do reasoning.

O evaluate.py guarda so a media harmonica, entao nao da para saber se o F1 baixo
e falta de conteudo (recall) ou excesso (precision). Essa distincao define a
direcao da Missao 7: uma pede acrescentar, a outra pede cortar.

Regenera a resposta com temperature=0 (mesmo do evaluate.py) para julgar o
mesmo texto. Roda so nas posicoes passadas na linha de comando.

Uso: python diag_f1.py 2 4 5 8 9 11
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve()
for cand in [Path.cwd()] + list(Path.cwd().parents):
    if (cand / "src" / "utils.py").exists():
        RAIZ = cand
        break
sys.path.insert(0, str(RAIZ / "src"))

from dotenv import load_dotenv
load_dotenv(RAIZ / ".env", override=True)

from langchain import hub
from langsmith import Client
from utils import get_llm
from metrics import evaluate_f1_score, evaluate_precision, evaluate_clarity

alvos = [int(a) for a in sys.argv[1:]] or [2, 4, 5, 8, 9, 11]

nivel_por_bug = {}
for linha in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8"):
    d = json.loads(linha)
    nivel_por_bug[d["inputs"]["bug_report"].strip()] = d["metadata"]["complexity"]

client = Client()
dataset = f"{os.getenv('LANGSMITH_PROJECT')}-eval"
exemplos = list(client.list_examples(dataset_name=dataset))

prompt = hub.pull(f"{os.getenv('USERNAME_LANGSMITH_HUB')}/bug_to_user_story_v2")
llm = get_llm(temperature=0)
chain = prompt | llm

for pos in alvos:
    ex = exemplos[pos - 1]
    bug = (ex.inputs or {}).get("bug_report", "")
    ref = (ex.outputs or {}).get("reference", "")
    nivel = nivel_por_bug.get(bug.strip(), "?")

    resposta = chain.invoke(ex.inputs).content
    f1 = evaluate_f1_score(bug, resposta, ref)
    pr = evaluate_precision(bug, resposta, ref)

    print("=" * 78)
    print(f"POS {pos} | nivel {nivel}")
    print(f"tamanho: gerado {len(resposta)} chars | referencia {len(ref)} chars "
          f"({len(resposta)/max(len(ref),1)*100:.0f}%)")
    print(f"bullets: gerado {resposta.count(chr(10) + '-')} | referencia {ref.count(chr(10) + '-')}")
    print(f"F1 {f1['score']:.2f}  = precision {f1['precision']:.2f} / recall {f1['recall']:.2f}")
    print(f"  F1 reasoning: {f1['reasoning']}")
    print(f"PRECISION {pr['score']:.2f}")
    print(f"  reasoning: {pr['reasoning']}")

"""
Descobre a ORDEM em que o evaluate.py itera os exemplos e associa cada
posicao [i/15] ao nivel de complexidade do JSONL.

Motivo: o evaluate.py usa client.list_examples(), cuja ordem nao e a do
arquivo. Sem esse mapa, as notas por exemplo impressas no log nao dizem
em qual nivel a nota caiu.

Custo: 0 chamadas de LLM. So uma leitura da API do LangSmith.
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
from langsmith import Client

load_dotenv(RAIZ / ".env")

# metadata NAO e enviado ao LangSmith pelo evaluate.py (create_example passa
# so inputs e outputs), entao a complexidade vem do arquivo local, casada
# pelo texto do bug_report.
nivel_por_bug = {}
for linha in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8"):
    d = json.loads(linha)
    nivel_por_bug[d["inputs"]["bug_report"].strip()] = d["metadata"]["complexity"]

dataset = f"{os.getenv('LANGSMITH_PROJECT')}-eval"
exemplos = list(Client().list_examples(dataset_name=dataset))

print(f"dataset: {dataset}")
print(f"exemplos na API: {len(exemplos)}\n")
print("pos\tnivel\t\tprimeiros 50 chars do bug")
linhas = []
for i, ex in enumerate(exemplos, 1):
    bug = (ex.inputs or {}).get("bug_report", "").strip()
    nivel = nivel_por_bug.get(bug, "DESCONHECIDO")
    linhas.append((i, nivel))
    print(f"{i}\t{nivel:9}\t{bug[:50]!r}")

print("\nmapa compacto (posicao -> nivel):")
print(json.dumps({str(i): n for i, n in linhas}, ensure_ascii=False))

faltando = [i for i, n in linhas if n == "DESCONHECIDO"]
if faltando:
    print(f"\nATENCAO: {len(faltando)} exemplos nao casaram com o JSONL: {faltando}")
    sys.exit(1)
print("\nOK: todos os 15 exemplos casaram com o JSONL.")

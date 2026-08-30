"""Shape check com bullets POR SECAO, para achar onde o complexo perde bullets."""
import json, sys
from pathlib import Path
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ / "src"))
from dotenv import load_dotenv
load_dotenv(RAIZ / ".env", override=True)
import yaml, re
from langchain_core.prompts import ChatPromptTemplate
from utils import get_llm

d = yaml.safe_load(open(RAIZ / "prompts/bug_to_user_story_v2.yml", encoding="utf-8"))
chain = ChatPromptTemplate.from_messages(
    [("system", d["system_prompt"]), ("human", d["user_prompt"])]) | get_llm(temperature=0)
dados = [json.loads(l) for l in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8")]

def por_secao(txt):
    atual, out = "(topo)", []
    for l in txt.splitlines():
        s = l.strip()
        if not s: continue
        if s.startswith("- "):
            if out and out[-1][0] == atual: out[-1][1] += 1
            else: out.append([atual, 1])
        elif (s.endswith(":") and len(s) < 60) or (s.startswith("===") and s.endswith("===")) or re.match(r"^[A-Z]\.\s", s):
            atual = s[:46]
    return out

for pos in [int(a) for a in sys.argv[1:]]:
    ex = dados[16 - pos - 1]
    ger = chain.invoke({"bug_report": ex["inputs"]["bug_report"]}).content
    ref = ex["outputs"]["reference"]
    tg = sum(n for _, n in por_secao(ger)); tr = sum(n for _, n in por_secao(ref))
    print("=" * 88)
    print(f"POS {pos} | {ex['metadata']['complexity']} | bullets gerado {tg} / referencia {tr}")
    print(f"  {'GERADO':<48}      {'REFERENCIA'}")
    g, r = por_secao(ger), por_secao(ref)
    for i in range(max(len(g), len(r))):
        ga = f"{g[i][1]:>2}  {g[i][0]}" if i < len(g) else ""
        ra = f"{r[i][1]:>2}  {r[i][0]}" if i < len(r) else ""
        print(f"  {ga:<50}  {ra}")

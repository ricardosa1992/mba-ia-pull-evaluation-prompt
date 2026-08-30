"""Despeja a saida gerada e a referencia lado a lado, sem juiz. Para eu LER."""
import json, sys
from pathlib import Path
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ / "src"))
from dotenv import load_dotenv
load_dotenv(RAIZ / ".env", override=True)
import yaml
from langchain_core.prompts import ChatPromptTemplate
from utils import get_llm
d = yaml.safe_load(open(RAIZ / "prompts/bug_to_user_story_v2.yml", encoding="utf-8"))
chain = ChatPromptTemplate.from_messages(
    [("system", d["system_prompt"]), ("human", d["user_prompt"])]) | get_llm(temperature=0)
dados = [json.loads(l) for l in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8")]
for pos in [int(a) for a in sys.argv[1:]]:
    ex = dados[16 - pos - 1]
    print("#" * 90); print(f"POS {pos} | {ex['metadata']['complexity']}")
    print("#" * 90)
    print("----- RELATO -----"); print(ex["inputs"]["bug_report"].strip())
    print("\n----- GERADO -----"); print(chain.invoke({"bug_report": ex["inputs"]["bug_report"]}).content)
    print("\n----- REFERENCIA -----"); print(ex["outputs"]["reference"].strip())

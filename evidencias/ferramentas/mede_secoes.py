import json, re, statistics
from pathlib import Path
RAIZ = Path.cwd()
dados = [json.loads(l) for l in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8")]

def por_secao(txt):
    """Conta bullets agrupados pela secao/rotulo que os precede."""
    atual, out = "(antes de qualquer secao)", {}
    for l in txt.splitlines():
        s = l.strip()
        if not s:
            continue
        if s.startswith("- "):
            out.setdefault(atual, 0)
            out[atual] += 1
        elif s.endswith(":") and len(s) < 60:
            atual = s
        elif s.startswith("===") and s.endswith("==="):
            atual = s
        elif re.match(r"^[A-Z]\.\s", s):          # grupos A. B. C. D. do complexo
            atual = "grupo " + s[0] + "."
    return out

print("### MEDIUM: bullets por secao")
for i, d in enumerate(dados, 1):
    if d["metadata"]["complexity"] != "medium":
        continue
    ps = por_secao(d["outputs"]["reference"])
    print(f"lin {i:>2}: total={sum(ps.values()):>2}  " + "  ".join(f"[{k.rstrip(':')}={v}]" for k, v in ps.items()))

print()
print("### COMPLEX: bullets por secao")
for i, d in enumerate(dados, 1):
    if d["metadata"]["complexity"] != "complex":
        continue
    ps = por_secao(d["outputs"]["reference"])
    print(f"lin {i}: total={sum(ps.values())}")
    for k, v in ps.items():
        print(f"      {v:>3} bullets  {k}")
    ref = d["outputs"]["reference"]
    print(f"      grupos de criterios (A./B./...): {len(re.findall(r'(?m)^[A-Z]\. ', ref))}")
    print(f"      tasks numeradas: {len(re.findall(r'(?m)^\d+\. ', ref))}")

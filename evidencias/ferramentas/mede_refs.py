"""
Mede as 15 referencias em BULLETS, SECOES e PALAVRAS POR BULLET.

Motivo: na Missao 3 eu calibrei por tamanho em chars, bati os chars e errei a
cobertura (3758 chars mas 20 bullets no lugar de 45). Char nao e a unidade certa.
"""
import json
import re
import statistics
from pathlib import Path

RAIZ = Path.cwd()
for c in [Path.cwd()] + list(Path.cwd().parents):
    if (c / "datasets/bug_to_user_story.jsonl").exists():
        RAIZ = c
        break

dados = [json.loads(l) for l in open(RAIZ / "datasets/bug_to_user_story.jsonl", encoding="utf-8")]

def bullets(txt):
    return [l.strip()[2:].strip() for l in txt.splitlines() if l.strip().startswith("- ")]

def secoes(txt):
    out = []
    for l in txt.splitlines():
        s = l.strip()
        if s.endswith(":") and not s.startswith("- ") and len(s) < 60:
            out.append(s)
        elif s.startswith("===") and s.endswith("==="):
            out.append(s)
    return out

print("=" * 100)
print("POR EXEMPLO")
print("=" * 100)
print(f"{'lin':>3} {'nivel':9} {'chars':>6} {'bull':>5} {'pal/bull':>9}  secoes")
por_nivel = {}
for i, d in enumerate(dados, 1):
    ref = d["outputs"]["reference"]
    nv = d["metadata"]["complexity"]
    bs = bullets(ref)
    pal = [len(b.split()) for b in bs]
    med = statistics.mean(pal) if pal else 0
    por_nivel.setdefault(nv, []).append((len(ref), len(bs), pal, secoes(ref)))
    print(f"{i:>3} {nv:9} {len(ref):>6} {len(bs):>5} {med:>9.1f}  {' | '.join(secoes(ref))[:70]}")

print()
print("=" * 100)
print("AGREGADO POR NIVEL")
print("=" * 100)
for nv in ["simple", "medium", "complex"]:
    itens = por_nivel[nv]
    bs = [x[1] for x in itens]
    todas_pal = [p for x in itens for p in x[2]]
    print(f"\n{nv.upper()} (n={len(itens)})")
    print(f"  bullets: min {min(bs)}  max {max(bs)}  mediana {statistics.median(bs):.0f}")
    print(f"  palavras por bullet: min {min(todas_pal)}  max {max(todas_pal)}  "
          f"media {statistics.mean(todas_pal):.1f}  mediana {statistics.median(todas_pal):.0f}  "
          f"p90 {sorted(todas_pal)[int(len(todas_pal)*0.9)]}")
    print(f"  bullets com mais de 12 palavras: "
          f"{sum(1 for p in todas_pal if p > 12)}/{len(todas_pal)} "
          f"({sum(1 for p in todas_pal if p > 12)/len(todas_pal)*100:.0f}%)")

print()
print("=" * 100)
print("MEDIUM: quais secoes aparecem em cada um dos 7")
print("=" * 100)
for i, d in enumerate(dados, 1):
    if d["metadata"]["complexity"] != "medium":
        continue
    ref = d["outputs"]["reference"]
    sec = secoes(ref)
    # secao secundaria = qualquer secao de criterios que nao a principal
    extra = [s for s in sec if s != "Critérios de Aceitação:" and "ontexto" not in s]
    ctx = [s for s in sec if "ontexto" in s]
    print(f"lin {i:>2}: bullets={len(bullets(ref))}  secundaria={extra if extra else 'NENHUMA'}  contexto={ctx}")

"""
Le o log do evaluate.py, casa cada linha [i/15] com o nivel de complexidade
(mapa vindo do map_ordem.py) e imprime medias por nivel.

Uso: python analisa_log.py <log> <mapa.json>
"""
import json
import re
import sys

log = open(sys.argv[1], encoding="utf-8", errors="replace").read()
mapa = json.load(open(sys.argv[2], encoding="utf-8"))

# Erros de juiz entram como score 0.0 na media (metrics.py devolve 0.0 em
# excecao), entao um 429 viraria "nota baixa" e nao "falha". Checar primeiro.
erros = re.findall(r"(❌ Erro ao avaliar.*|⚠️  Erro ao avaliar exemplo.*|Não foi possível extrair JSON.*)", log)
print(f"linhas de erro no log: {len(erros)}")
for e in erros[:10]:
    print(f"  {e[:140]}")
if not erros:
    print("  nenhuma. As notas nao estao contaminadas por falha de API.")

linhas = re.findall(r"\[(\d+)/(\d+)\] F1:([\d.]+) Clarity:([\d.]+) Precision:([\d.]+)", log)
print(f"\nexemplos pontuados: {len(linhas)} (esperado 15)")

por_nivel = {}
print("\npos nivel      F1     Clarity  Precision")
for pos, _tot, f1, cl, pr in linhas:
    nivel = mapa.get(pos, "?")
    f1, cl, pr = float(f1), float(cl), float(pr)
    por_nivel.setdefault(nivel, []).append((f1, cl, pr))
    marca = "  <-- abaixo de 0.8" if min(f1, cl, pr) < 0.8 else ""
    print(f"{pos:>3} {nivel:10} {f1:.2f}   {cl:.2f}     {pr:.2f}{marca}")

def med(vals, idx):
    return sum(v[idx] for v in vals) / len(vals)

print("\n=== MEDIA POR NIVEL ===")
print("nivel      n    F1     Clarity  Precision   Helpfulness  Correctness")
for nivel in ["simple", "medium", "complex"]:
    vals = por_nivel.get(nivel)
    if not vals:
        continue
    f1, cl, pr = med(vals, 0), med(vals, 1), med(vals, 2)
    print(f"{nivel:10} {len(vals):<4} {f1:.3f}  {cl:.3f}    {pr:.3f}       "
          f"{(cl+pr)/2:.3f}        {(f1+pr)/2:.3f}")

todos = [v for vals in por_nivel.values() for v in vals]
if todos:
    f1, cl, pr = med(todos, 0), med(todos, 1), med(todos, 2)
    print(f"{'GERAL':10} {len(todos):<4} {f1:.3f}  {cl:.3f}    {pr:.3f}       "
          f"{(cl+pr)/2:.3f}        {(f1+pr)/2:.3f}")

print("\n=== MENORES NOTAS INDIVIDUAIS ===")
plano = [(float(f1), float(cl), float(pr), pos, mapa.get(pos, "?"))
         for pos, _t, f1, cl, pr in linhas]
for metrica, idx in [("F1", 0), ("Clarity", 1), ("Precision", 2)]:
    piores = sorted(plano, key=lambda x: x[idx])[:4]
    alvo = ", ".join(f"pos{p[3]}/{p[4]}={p[idx]:.2f}" for p in piores)
    print(f"{metrica:10} piores: {alvo}")

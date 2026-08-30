"""
Checagem de mutacao dos 6 testes: quebra o prompt de proposito e confirma
que o teste correspondente REPROVA. Nao toca no arquivo real do projeto.
"""

import copy
import sys
import tempfile
from pathlib import Path

RAIZ = Path.cwd()
for cand in [Path.cwd()] + list(Path.cwd().parents):
    if (cand / "src" / "utils.py").exists():
        RAIZ = cand
        break

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))

import tests.test_prompts as tp

original = tp.load_prompts(tp.PROMPT_FILE)
suite = tp.TestPrompts()


def esperar_falha(nome, metodo, dados):
    try:
        metodo(dados)
    except AssertionError as e:
        print(f"  OK   {nome} reprovou como esperado")
        print(f"       motivo: {str(e).splitlines()[0][:90]}")
        return True
    print(f"  FALHA {nome} PASSOU com prompt quebrado (teste nao detecta nada)")
    return False


def mutar(**mudancas):
    d = copy.deepcopy(original)
    d.update(mudancas)
    return d


resultados = []

print("1. system_prompt vazio")
resultados.append(esperar_falha(
    "test_prompt_has_system_prompt",
    suite.test_prompt_has_system_prompt,
    mutar(system_prompt="   ")))

print("\n2. sem persona definida")
resultados.append(esperar_falha(
    "test_prompt_has_role_definition",
    suite.test_prompt_has_role_definition,
    mutar(system_prompt="Transforme o relato de bug em uma tarefa.")))

print("\n3. persona sem cargo reconhecivel")
resultados.append(esperar_falha(
    "test_prompt_has_role_definition",
    suite.test_prompt_has_role_definition,
    mutar(system_prompt="Você é um ajudante simpático.")))

print("\n4. sem formato de saida")
resultados.append(esperar_falha(
    "test_prompt_mentions_format",
    suite.test_prompt_mentions_format,
    mutar(system_prompt="Você é um Product Owner. Escreva algo sobre o bug.")))

print("\n5. sem exemplos few-shot")
resultados.append(esperar_falha(
    "test_prompt_has_few_shot_examples",
    suite.test_prompt_has_few_shot_examples,
    mutar(system_prompt=original["system_prompt"].split("EXEMPLOS")[0])))

print("\n6. apenas 1 tecnica")
resultados.append(esperar_falha(
    "test_minimum_techniques",
    suite.test_minimum_techniques,
    mutar(techniques_applied=["Few-shot Learning"])))

print("\n7. arquivo com [TODO] sobrando")
tmp = Path(tempfile.gettempdir()) / "prompt_com_todo.yml"
tmp.write_text("system_prompt: |\n  Você é um Product Owner.\n  [TODO] escrever os exemplos\n",
               encoding="utf-8")
guardado = tp.PROMPT_FILE
tp.PROMPT_FILE = tmp
try:
    resultados.append(esperar_falha(
        "test_prompt_no_todos", lambda _: suite.test_prompt_no_todos(), original))
finally:
    tp.PROMPT_FILE = guardado
    tmp.unlink(missing_ok=True)

print("\n" + "=" * 60)
if all(resultados):
    print(f"TODAS AS {len(resultados)} MUTACOES FORAM DETECTADAS. Testes tem dentes.")
    sys.exit(0)
print(f"{resultados.count(False)} de {len(resultados)} mutacoes passaram sem ser detectadas.")
sys.exit(1)

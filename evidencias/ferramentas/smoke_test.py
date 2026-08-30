"""
Smoke test da Missao 0: valida ambiente, credenciais e conectividade.

Uso (na raiz do projeto, com o venv):
    venv/Scripts/python.exe <caminho>/smoke_test.py

Nao imprime segredos, apenas se estao presentes e o tamanho da chave.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
# Descobre a raiz do projeto: onde existe a pasta src/
for candidate in [Path.cwd()] + list(Path.cwd().parents):
    if (candidate / "src" / "utils.py").exists():
        PROJECT_ROOT = candidate
        break

sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

failures = []


def line(char="=", width=60):
    print(char * width)


def mask(value):
    if not value:
        return "AUSENTE"
    return f"presente ({len(value)} chars)"


# ---------------------------------------------------------------- 1. pacotes
line()
print("1. PACOTES INSTALADOS")
line()
try:
    import langchain
    import langsmith
    import pydantic
    import yaml
    import pytest

    print(f"   langchain  {langchain.__version__}")
    print(f"   langsmith  {langsmith.__version__}")
    print(f"   pydantic   {pydantic.__version__}")
    print(f"   pyyaml     {yaml.__version__}")
    print(f"   pytest     {pytest.__version__}")
    print("   OK")
except Exception as exc:
    failures.append(f"import de pacotes: {exc}")
    print(f"   FALHA: {exc}")

# ------------------------------------------------------- 2. variaveis de ambiente
line()
print("2. VARIAVEIS DE AMBIENTE (.env)")
line()

provider = (os.getenv("LLM_PROVIDER") or "").lower()
env_report = {
    "LANGSMITH_API_KEY": mask(os.getenv("LANGSMITH_API_KEY")),
    "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT") or "AUSENTE",
    "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING") or "AUSENTE",
    "USERNAME_LANGSMITH_HUB": os.getenv("USERNAME_LANGSMITH_HUB") or "AUSENTE",
    "LLM_PROVIDER": provider or "AUSENTE",
    "LLM_MODEL": os.getenv("LLM_MODEL") or "AUSENTE",
    "EVAL_MODEL": os.getenv("EVAL_MODEL") or "AUSENTE",
}
if provider == "openai":
    env_report["OPENAI_API_KEY"] = mask(os.getenv("OPENAI_API_KEY"))
elif provider in ("google", "gemini"):
    env_report["GOOGLE_API_KEY"] = mask(os.getenv("GOOGLE_API_KEY"))

for key, value in env_report.items():
    status = "x" if value == "AUSENTE" else "v"
    print(f"   [{status}] {key}: {value}")
    if value == "AUSENTE":
        failures.append(f"variavel nao configurada: {key}")

# ------------------------------------------------------------- 3. LangSmith
line()
print("3. CONEXAO COM O LANGSMITH")
line()
if not os.getenv("LANGSMITH_API_KEY"):
    print("   PULADO: LANGSMITH_API_KEY ausente")
else:
    try:
        from langsmith import Client

        client = Client()
        datasets = list(client.list_datasets(limit=5))
        print(f"   Autenticado. Datasets visiveis: {len(datasets)}")
        for ds in datasets:
            print(f"      - {ds.name}")
        print("   OK")
    except Exception as exc:
        failures.append(f"conexao LangSmith: {exc}")
        print(f"   FALHA: {exc}")

# ------------------------------------------------------------- 4. LLM
line()
print("4. CHAMADA NO LLM (get_llm do src/utils.py)")
line()
provider_key = os.getenv("OPENAI_API_KEY") if provider == "openai" else os.getenv("GOOGLE_API_KEY")
if not provider_key:
    print(f"   PULADO: chave do provider '{provider}' ausente")
else:
    try:
        from utils import get_llm

        llm = get_llm()
        resposta = llm.invoke("Responda apenas com a palavra: pong")
        print(f"   Modelo: {os.getenv('LLM_MODEL')}")
        print(f"   Resposta: {resposta.content.strip()[:120]}")
        print("   OK")
    except Exception as exc:
        failures.append(f"chamada LLM: {exc}")
        print(f"   FALHA: {exc}")

# ------------------------------------------------- 5. LLM de avaliacao (juiz)
line()
print("5. CHAMADA NO LLM DE AVALIACAO (get_eval_llm)")
line()
if not provider_key:
    print(f"   PULADO: chave do provider '{provider}' ausente")
else:
    try:
        from utils import get_eval_llm

        judge = get_eval_llm()
        resposta = judge.invoke('Retorne apenas este JSON: {"score": 1.0}')
        print(f"   Modelo: {os.getenv('EVAL_MODEL')}")
        print(f"   Resposta: {resposta.content.strip()[:120]}")
        print("   OK")
    except Exception as exc:
        failures.append(f"chamada LLM de avaliacao: {exc}")
        print(f"   FALHA: {exc}")

# ---------------------------------------------------------- 6. arquivos base
line()
print("6. ARQUIVOS DO PROJETO")
line()
for rel in [
    ".env",
    "requirements.txt",
    "datasets/bug_to_user_story.jsonl",
    "prompts/bug_to_user_story_v1.yml",
    "src/evaluate.py",
    "src/metrics.py",
    "src/utils.py",
]:
    exists = (PROJECT_ROOT / rel).exists()
    print(f"   [{'v' if exists else 'x'}] {rel}")
    if not exists:
        failures.append(f"arquivo faltando: {rel}")

dataset_path = PROJECT_ROOT / "datasets" / "bug_to_user_story.jsonl"
if dataset_path.exists():
    total = sum(1 for linha in dataset_path.read_text(encoding="utf-8").splitlines() if linha.strip())
    print(f"   dataset com {total} exemplos (esperado: 15)")
    if total != 15:
        failures.append(f"dataset com {total} exemplos, esperado 15")

# ------------------------------------------------------------------ resumo
line()
if failures:
    print(f"RESULTADO: {len(failures)} pendencia(s)")
    for item in failures:
        print(f"   - {item}")
    line()
    sys.exit(1)

print("RESULTADO: AMBIENTE PRONTO. Missao 0 concluida.")
line()
sys.exit(0)

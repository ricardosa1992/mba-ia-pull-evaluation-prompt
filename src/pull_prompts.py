"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from datetime import date

import yaml
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"
ROOT_KEY = "bug_to_user_story_v1"


def _block_style(dumper, data):
    """Grava textos com quebra de linha em bloco literal (|), para o YAML ficar legível."""
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _block_style)


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt de baixa qualidade do Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"Fazendo pull de: {SOURCE_PROMPT}")

    try:
        prompt = hub.pull(SOURCE_PROMPT)

        templates = {}
        for message in prompt.messages:
            campo = "system_prompt" if type(message).__name__.startswith("System") else "user_prompt"
            templates[campo] = message.prompt.template

    except Exception as e:
        print(f"❌ Erro ao fazer pull: {e}")
        print("   Verifique a LANGSMITH_API_KEY no .env e se o prompt está público.")
        return False

    if not templates.get("system_prompt"):
        print("❌ O prompt baixado não tem mensagem de system.")
        return False

    metadata = prompt.metadata or {}
    prompt_data = {
        ROOT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": templates["system_prompt"],
            "user_prompt": templates.get("user_prompt", ""),
            "version": "v1",
            "source": {
                "hub_prompt": SOURCE_PROMPT,
                "commit_hash": metadata.get("lc_hub_commit_hash", ""),
                "pulled_at": date.today().isoformat(),
            },
        }
    }

    if not save_yaml(prompt_data, OUTPUT_FILE):
        return False

    print(f"   ✓ Variáveis de entrada: {prompt.input_variables}")
    print(f"   ✓ Prompt salvo em: {OUTPUT_FILE}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído. Próximo passo: criar prompts/bug_to_user_story_v2.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())

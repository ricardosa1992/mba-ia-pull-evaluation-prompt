"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_REPO = "bug_to_user_story_v2"


def build_template(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate a partir do YAML (system + user)."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, erros = validate_prompt_structure(prompt_data)

    # Checagem específica do push: o evaluate.py injeta apenas {bug_report},
    # então qualquer outra variável no template quebra a avaliação com KeyError.
    try:
        variaveis = build_template(prompt_data).input_variables
        if variaveis != ["bug_report"]:
            erros.append(f"variáveis devem ser ['bug_report'], encontradas: {variaveis}")
    except Exception as e:
        erros.append(f"template não compila: {e}")

    return (len(erros) == 0, erros)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    tecnicas = prompt_data.get("techniques_applied", [])
    readme = "{}\n\nTécnicas aplicadas:\n{}".format(
        prompt_data["description"],
        "\n".join(f"- {t}" for t in tecnicas),
    )

    print(f"Fazendo push de: {prompt_name}")

    try:
        url = hub.push(
            prompt_name,
            build_template(prompt_data),
            new_repo_is_public=True,
            new_repo_description=prompt_data["description"],
            readme=readme,
            tags=prompt_data.get("tags", []),
        )
    except Exception as e:
        print(f"❌ Erro ao fazer push: {e}")
        print("   Verifique se o USERNAME_LANGSMITH_HUB do .env é o handle do seu workspace.")
        return False

    print(f"   ✓ Commit publicado: {url}")
    print(f"   ✓ Técnicas nos metadados: {', '.join(tecnicas)}")
    return True


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompt_data = load_yaml(PROMPT_FILE)
    if prompt_data is None:
        return 1

    valido, erros = validate_prompt(prompt_data)
    if not valido:
        print("❌ Prompt inválido, push cancelado:")
        for erro in erros:
            print(f"   - {erro}")
        return 1

    print(f"   ✓ {PROMPT_FILE} validado\n")

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_REPO}"
    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    # Confirma que o prompt está público e volta do Hub pronto para o evaluate.py
    info = Client().get_prompt(prompt_name)
    print(f"   ✓ Público: {getattr(info, 'is_public', 'desconhecido')}")
    print(f"   ✓ Variáveis no Hub: {hub.pull(prompt_name).input_variables}")

    print("\n✅ Push concluído. Próximo passo: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

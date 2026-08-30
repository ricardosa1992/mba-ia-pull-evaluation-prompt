"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import re
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture
def prompt():
    """Prompt otimizado v2, carregado do YAML."""
    return load_prompts(PROMPT_FILE)

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "campo system_prompt não existe no YAML"
        assert prompt["system_prompt"].strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt["system_prompt"]

        abre_persona = re.search(r"você é (um|uma|o|a)\s+\w", system_prompt, re.IGNORECASE)
        assert abre_persona, "system_prompt não abre com uma definição de persona"

        cargos = ["product owner", "product manager", "analista", "engenheiro", "especialista"]
        assert any(c in system_prompt.lower() for c in cargos), \
            f"a persona não cita um cargo reconhecível: {cargos}"

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt["system_prompt"].lower()

        user_story = all(t in system_prompt for t in ["como um", "eu quero", "para que"])
        criterios = "critérios de aceitação" in system_prompt
        markdown = "markdown" in system_prompt

        assert (user_story and criterios) or markdown, \
            "o prompt não exige o formato de User Story padrão nem Markdown"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt["system_prompt"]

        assert len(re.findall(r"Exemplo \d", system_prompt)) >= 2, \
            "menos de 2 exemplos rotulados no prompt"
        assert system_prompt.count("Entrada:") >= 2, "menos de 2 blocos de Entrada:"
        assert system_prompt.count("Saída:") >= 2, "menos de 2 blocos de Saída:"

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        # Lê o arquivo cru para pegar TODO também em comentários do YAML.
        # Busca 'TODO' em maiúsculas: em português 'todos' contém 'todo',
        # então uma busca case-insensitive daria falso positivo.
        conteudo = PROMPT_FILE.read_text(encoding="utf-8")

        assert "[TODO]" not in conteudo, "ainda existe [TODO] no arquivo"
        assert not re.search(r"\bTODO\b", conteudo), "ainda existe TODO no arquivo"
        assert not re.search(r"\bFIXME\b", conteudo), "ainda existe FIXME no arquivo"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        tecnicas = prompt.get("techniques_applied", [])

        assert isinstance(tecnicas, list), "techniques_applied não é uma lista"
        assert len(tecnicas) >= 2, f"mínimo de 2 técnicas, encontradas: {len(tecnicas)}"

        # Reforço: a validação oficial do projeto também precisa passar
        valido, erros = validate_prompt_structure(prompt)
        assert valido, f"validate_prompt_structure reprovou: {erros}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Gera as imagens da entrega a partir dos links publicos do LangSmith.

POR QUE ASSIM
A entrega pede screenshot das 5 notas e de 3 traces. Em vez de printar a tela na
mao, este script abre as MESMAS paginas publicas listadas em
evidencias/links-publicos.md com o Chrome em modo headless e salva cada uma em
evidencias/capturas/. Duas vantagens: a imagem e reproduzivel por qualquer um que
rode o comando, e ela sai de uma sessao sem login nenhum, o que e a prova visual
de que o link abre em janela anonima.

Nao instala nada. Usa o Chrome que ja esta na maquina, com --headless=new e um
perfil descartavel no diretorio temporario, para nao mexer no perfil do usuario.

O que captura:
    01-experimento-5-metricas.png   aba Experiments: as 5 medias do experimento
    02-dataset-15-exemplos.png      aba Examples: os 15 exemplos do dataset
    03-notas-por-exemplo.png        tabela do experimento: 15 linhas x 5 notas
    04-trace-simple.png             trace do exemplo simple
    05-trace-medium.png             trace do exemplo medium
    06-trace-complex.png            trace do exemplo complex

USO
    python evidencias/ferramentas/captura_paginas.py
    python evidencias/ferramentas/captura_paginas.py --espera 90
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parents[2]
ARQ_ESTADO = RAIZ / "evidencias" / "experimento-publicado.json"
DIR_SAIDA = RAIZ / "evidencias" / "capturas"

CAMINHOS_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def acha_chrome():
    for c in CAMINHOS_CHROME:
        if c and Path(c).exists():
            return c
    achado = shutil.which("chrome") or shutil.which("google-chrome")
    if achado:
        return achado
    raise SystemExit("ERRO: Chrome nao encontrado. Ajuste CAMINHOS_CHROME.")


def monta_paginas(estado):
    """Monta a lista (arquivo, titulo, url) a partir do estado da publicacao."""
    base_publica = estado["dataset_publico"]["url"]  # .../public/<token>/d
    sessao = parse_qs(urlparse(estado["url_experimento"]).query)["selectedSessions"][0]

    paginas = [
        (
            "01-experimento-5-metricas.png",
            "aba Experiments, com as 5 medias do experimento",
            base_publica,
            (1600, 1200),
        ),
        (
            "02-dataset-15-exemplos.png",
            "aba Examples, com os 15 exemplos do dataset",
            f"{base_publica}?tab=2",
            (1600, 1200),
        ),
        (
            "03-notas-por-exemplo.png",
            "tabela do experimento: 15 linhas com as 5 notas cada",
            f"{base_publica}/compare?selectedSessions={sessao}",
            (1600, 1200),
        ),
    ]

    numero = {"simple": "04", "medium": "05", "complex": "06"}
    for t in estado.get("traces", []):
        nivel = t["nivel"]
        paginas.append(
            (
                f"{numero.get(nivel, '07')}-trace-{nivel}.png",
                f"trace do exemplo {nivel} (posicao {t['pos']} no .jsonl)",
                t["url_publica"],
                (1600, 1400),
            )
        )
    return paginas


def captura(chrome, url, destino, tamanho, espera, indice):
    """Uma instancia por captura, cada uma com seu perfil descartavel: o Chrome
    trava o perfil enquanto o processo nao morre, e reusar da erro silencioso."""
    perfil = Path(tempfile.gettempdir()) / f"claude-captura-perfil-{indice}"
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        f"--user-data-dir={perfil}",
        f"--window-size={tamanho[0]},{tamanho[1]}",
        f"--virtual-time-budget={espera * 1000}",
        f"--screenshot={destino}",
        url,
    ]
    subprocess.run(cmd, capture_output=True, timeout=espera + 120)
    return destino.exists()


def escreve_leiame(paginas, estado):
    linhas = [
        "# Capturas da entrega",
        "",
        "Imagens geradas por `evidencias/ferramentas/captura_paginas.py`, que abre",
        "os links publicos de `evidencias/links-publicos.md` no Chrome headless,",
        "**sem nenhum login**. Rodar o script de novo refaz todas elas.",
        "",
        f"Experimento: `{estado['experimento']}`",
        f"Prompt: `{estado['prompt']}`, commit `{estado['prompt_commit']}`",
        "",
        "| Arquivo | O que mostra |",
        "|---|---|",
    ]
    for arquivo, titulo, _url, _tam in paginas:
        linhas.append(f"| `{arquivo}` | {titulo} |")
    linhas += [
        "",
        "Duas observacoes para quem for olhar as imagens:",
        "",
        "1. A run raiz aparece com o nome **Target**. E o nome que o runner do",
        "   `langsmith.evaluation.evaluate` da para a funcao alvo; o prompt de",
        "   verdade esta no filho `ChatOpenAI` e na descricao do experimento.",
        "2. O cabecalho da aba Experiments mostra a media do servidor, que conta",
        "   14 das 15 notas por uma estatistica materializada desatualizada. As 15",
        "   linhas com nota estao todas em `03-notas-por-exemplo.png`. As duas",
        "   contas passam de 0.8; a divergencia esta explicada em",
        "   `links-publicos.md`.",
        "",
    ]
    (DIR_SAIDA / "README.md").write_text("\n".join(linhas), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Captura as paginas publicas")
    p.add_argument(
        "--espera",
        type=int,
        default=60,
        help="segundos de tempo virtual por pagina (padrao 60)",
    )
    args = p.parse_args()

    if not ARQ_ESTADO.exists():
        print(f"ERRO: {ARQ_ESTADO} nao existe. Rode o publica_experimento.py antes.")
        return 1

    estado = json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))
    if not estado.get("dataset_publico"):
        print("ERRO: o estado nao tem link publico. Rode com --so-links antes.")
        return 1

    chrome = acha_chrome()
    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    paginas = monta_paginas(estado)

    print(f"Chrome: {chrome}")
    print(f"Saida : {DIR_SAIDA.relative_to(RAIZ)}")
    print(f"Espera: {args.espera}s por pagina\n")

    falhas = 0
    for i, (arquivo, titulo, url, tamanho) in enumerate(paginas, 1):
        destino = DIR_SAIDA / arquivo
        if destino.exists():
            destino.unlink()
        ok = captura(chrome, url, destino, tamanho, args.espera, i)
        tam = f"{destino.stat().st_size // 1024} KB" if ok else "FALHOU"
        print(f"[{i}/{len(paginas)}] {arquivo:<34} {tam:>8}  {titulo}")
        if not ok:
            falhas += 1

    escreve_leiame(paginas, estado)
    print(f"\nEscrito: {(DIR_SAIDA / 'README.md').relative_to(RAIZ)}")
    if falhas:
        print(f"ATENCAO: {falhas} captura(s) falharam.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

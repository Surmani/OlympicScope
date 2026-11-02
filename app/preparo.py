"""Preparo do banco na nuvem — unidade 6.4.

Na hospedagem (Streamlit Community Cloud) o banco não existe: ``data/`` não
vai para o Git, e o disco do servidor é temporário (some quando o app dorme
ou reinicia). Este módulo gera o banco rodando o ``executar.py`` como um
processo separado, uma vez por inicialização do servidor.

Regras e motivos
----------------

- Só gera se o secret ``gerar_banco_se_faltar = true`` estiver ligado.
  Motivo: na máquina de quem desenvolve, o app continua sem criar banco
  (regra da spec); a exceção vale só onde ela foi ligada de propósito, no
  painel da hospedagem.
- Roda o ``executar.py`` em outro processo, não importa o ``pipeline``.
  Motivo: o app e o pipeline continuam separados, e o pipeline roda
  exatamente como roda na linha de comando (mesmas verificações).
- ``st.cache_resource``: uma vez por processo do servidor, e com trava.
  Motivo: dois visitantes chegando juntos não podem gerar o banco ao mesmo
  tempo (o DuckDB aceita um único processo escrevendo).

Critérios de aceite (verificados em ``tests/test_app_paginas.py``)
-----------------------------------------------------------------

1. Sem o secret, o app sem banco só avisa e não gera nada.
2. Com o secret, o app sem banco gera o banco e abre a primeira página.
3. Se a geração falhar, o app mostra o fim da saída do pipeline e para.
"""

import subprocess
import sys
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

RAIZ = Path(__file__).resolve().parent.parent


def geracao_ligada() -> bool:
    """Lê o secret gerar_banco_se_faltar; sem arquivo de secrets, é False."""
    try:
        return bool(st.secrets.get("gerar_banco_se_faltar", False))
    except StreamlitSecretNotFoundError:  # sem secrets.toml (ex.: na máquina local)
        return False


def executar_pipeline() -> subprocess.CompletedProcess:
    """Roda ``python executar.py`` na raiz do projeto e devolve o resultado."""
    return subprocess.run(
        [sys.executable, str(RAIZ / "executar.py")],
        check=False,  # o código de saída é tratado por quem chama
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


@st.cache_resource(show_spinner=False)
def gerar_banco() -> tuple[int, str]:
    """Gera o banco uma vez por processo; devolve (código de saída, saída)."""
    resultado = executar_pipeline()
    return resultado.returncode, (resultado.stdout or "") + (resultado.stderr or "")

"""Testes de ui.py.

Nenhum teste abre data/olympics.duckdb nem sobe o servidor da UI: o caminho
do banco é trocado por um caminho inexistente em tmp_path.
"""

import ast
from pathlib import Path

import pytest

import ui

RAIZ = Path(__file__).resolve().parent.parent


def modulos_importados(arquivo):
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module.split(".")[0])
    return nomes


def test_sem_banco_encerra_com_codigo_1_sem_criar_nada(tmp_path, monkeypatch, capsys):
    banco = tmp_path / "data" / "olympics.duckdb"
    monkeypatch.setattr(ui, "CAMINHO_BANCO", banco)

    with pytest.raises(SystemExit) as saida_programa:
        ui.main()

    assert saida_programa.value.code == 1
    saida = capsys.readouterr()
    assert saida.out == ""
    assert str(banco) in saida.err
    assert "uv run python -m pipeline.ingestao" in saida.err
    assert not banco.exists()
    assert not banco.parent.exists()


def test_ui_nao_importa_pipeline():
    assert "pipeline" not in modulos_importados(RAIZ / "ui.py")


def test_pipeline_nao_importa_ui():
    for arquivo in (RAIZ / "pipeline").glob("*.py"):
        assert "ui" not in modulos_importados(arquivo), arquivo.name

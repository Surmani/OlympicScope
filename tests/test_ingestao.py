"""Testes de pipeline/ingestao.py.

Nenhum teste lê raw/: as pastas de origem são inventadas em tmp_path.
"""

import pytest

from pipeline import ingestao


def criar_arquivos(pasta, nomes):
    for nome in nomes:
        (pasta / nome).write_text("inventado\n", encoding="utf-8")


def test_todos_presentes_nao_falta_nada(tmp_path, capsys):
    criar_arquivos(tmp_path, ingestao.ARQUIVOS)

    assert ingestao.arquivos_faltando(tmp_path) == []
    ingestao.validar_arquivos(tmp_path)

    saida = capsys.readouterr()
    assert saida.out == ""
    assert saida.err == ""


def test_falta_um_arquivo(tmp_path):
    criar_arquivos(tmp_path, ["athlete_events.csv"])

    assert ingestao.arquivos_faltando(tmp_path) == ["noc_regions.csv"]


def test_faltam_todos_na_ordem_de_arquivos(tmp_path):
    assert ingestao.arquivos_faltando(tmp_path) == list(ingestao.ARQUIVOS)


def test_pasta_com_nome_de_arquivo_conta_como_faltando(tmp_path):
    criar_arquivos(tmp_path, ["noc_regions.csv"])
    (tmp_path / "athlete_events.csv").mkdir()

    assert ingestao.arquivos_faltando(tmp_path) == ["athlete_events.csv"]


def test_validar_encerra_com_codigo_1_e_lista_em_stderr(tmp_path, capsys):
    with pytest.raises(SystemExit) as saida_programa:
        ingestao.validar_arquivos(tmp_path)

    assert saida_programa.value.code == 1

    saida = capsys.readouterr()
    assert saida.out == ""
    assert str(tmp_path) in saida.err
    for nome in ingestao.ARQUIVOS:
        assert nome in saida.err

"""Testes de pipeline/marts.py.

Nenhum teste abre data/olympics.duckdb nem lê raw/: a refined e os SQL de
mart são inventados em tmp_path.
"""

import duckdb
import pytest

from pipeline import db, marts


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Banco temporário com uma refined inventada e uma pasta de marts vazia."""
    banco = tmp_path / "teste.duckdb"
    conexao = duckdb.connect(str(banco))
    conexao.execute("CREATE SCHEMA refined")
    conexao.execute(
        "CREATE TABLE refined.athlete_results AS SELECT * FROM (VALUES "
        "(1, 'BRA', 'Gold'), (2, 'BRA', NULL), (3, 'ARG', 'Silver')"
        ") AS t(athlete_id, noc, medal)"
    )
    conexao.close()

    pasta = tmp_path / "marts"
    pasta.mkdir()
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)
    monkeypatch.setattr(marts, "PASTA_SQL", pasta)
    return banco, pasta


def test_cria_marts_e_imprime_contagens(ambiente, capsys):
    banco, pasta = ambiente
    (pasta / "01_atletas_por_noc.sql").write_text(
        "CREATE OR REPLACE TABLE marts.atletas_por_noc AS "
        "SELECT noc, COUNT(DISTINCT athlete_id) AS atletas "
        "FROM refined.athlete_results GROUP BY noc",
        encoding="utf-8",
    )
    marts.main()

    assert capsys.readouterr().out == "marts.atletas_por_noc: 2 linhas\n"
    conexao = duckdb.connect(str(banco), read_only=True)
    try:
        assert conexao.execute(
            "SELECT noc, atletas FROM marts.atletas_por_noc ORDER BY noc"
        ).fetchall() == [("ARG", 1), ("BRA", 2)]
    finally:
        conexao.close()


def test_rodar_duas_vezes_imprime_igual(ambiente, capsys):
    _, pasta = ambiente
    (pasta / "01_medalhas.sql").write_text(
        "CREATE OR REPLACE TABLE marts.medalhas AS "
        "SELECT * FROM refined.athlete_results WHERE medal IS NOT NULL",
        encoding="utf-8",
    )
    marts.main()
    primeira = capsys.readouterr().out
    marts.main()
    segunda = capsys.readouterr().out

    assert primeira == segunda == "marts.medalhas: 2 linhas\n"


def test_pasta_vazia_encerra_com_codigo_1_sem_criar_banco(
    tmp_path, monkeypatch, capsys
):
    banco = tmp_path / "data" / "nao_existe.duckdb"
    pasta = tmp_path / "marts_vazia"
    pasta.mkdir()
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)
    monkeypatch.setattr(marts, "PASTA_SQL", pasta)

    with pytest.raises(SystemExit) as saida_programa:
        marts.main()

    assert saida_programa.value.code == 1
    saida = capsys.readouterr()
    assert saida.out == ""
    assert str(pasta) in saida.err
    assert not banco.exists()
    assert not banco.parent.exists()

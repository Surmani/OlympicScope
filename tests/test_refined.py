"""Testes de pipeline/refined.py e dos SQL de sql/refined/.

Nenhum teste abre data/olympics.duckdb nem lê raw/: o schema raw é
inventado em DuckDB em memória ou em tmp_path. Os SQL testados são os
arquivos reais de sql/refined/.
"""

import duckdb
import pytest

from pipeline import db, refined


@pytest.fixture
def con():
    conexao = duckdb.connect()
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute(
        "CREATE TABLE raw.noc_regions AS SELECT * FROM (VALUES "
        "('BRA', 'Brazil', ''), "
        "(' URS ', ' Russia ', ' antiga '), "
        "('ROT', 'NA', 'Refugee Olympic Team'), "
        "('SIN', 'Singapore', '')"
        ') AS t("NOC", "region", "notes")'
    )
    yield conexao
    conexao.close()


def linhas(con, sql):
    return con.execute(sql).fetchall()


# --- executor ---------------------------------------------------------------


def test_nome_tabela_tira_prefixo():
    assert refined.nome_tabela("01_noc_regions.sql") == "noc_regions"
    assert refined.nome_tabela("12_athlete_results.sql") == "athlete_results"


def test_executa_em_ordem_de_nome(tmp_path):
    (tmp_path / "02_segunda.sql").write_text(
        "CREATE OR REPLACE TABLE refined.segunda AS SELECT COUNT(*) AS n FROM refined.primeira",
        encoding="utf-8",
    )
    (tmp_path / "01_primeira.sql").write_text(
        "CREATE OR REPLACE TABLE refined.primeira AS SELECT 1 AS x",
        encoding="utf-8",
    )
    conexao = duckdb.connect()
    try:
        contagens = refined.executar(conexao, tmp_path)
    finally:
        conexao.close()

    assert list(contagens) == ["refined.primeira", "refined.segunda"]


def test_sql_que_nao_cria_a_tabela_do_nome_gera_erro(tmp_path):
    (tmp_path / "01_esperada.sql").write_text(
        "CREATE OR REPLACE TABLE refined.outra AS SELECT 1 AS x", encoding="utf-8"
    )
    conexao = duckdb.connect()
    try:
        with pytest.raises(RuntimeError, match="refined.esperada"):
            refined.executar(conexao, tmp_path)
    finally:
        conexao.close()


def test_main_duas_vezes_imprime_igual(tmp_path, monkeypatch, capsys):
    banco = tmp_path / "teste.duckdb"
    conexao = duckdb.connect(str(banco))
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute(
        "CREATE TABLE raw.noc_regions AS SELECT * FROM (VALUES ('SIN', 'Singapore', '')) AS t(\"NOC\", \"region\", \"notes\")"
    )
    conexao.close()
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)

    refined.main()
    primeira = capsys.readouterr().out
    refined.main()
    segunda = capsys.readouterr().out

    assert primeira == segunda
    assert "refined.noc_regions: 2 linhas\n" in primeira


# --- refined.noc_regions ------------------------------------------------------


def test_noc_regions_nao_descarta_e_acrescenta_sgp(con):
    contagens = refined.executar(con, refined.PASTA_SQL)

    assert contagens["refined.noc_regions"] == 4 + 1
    assert linhas(con, "SELECT noc FROM refined.noc_regions ORDER BY noc") == [
        ("BRA",),
        ("ROT",),
        ("SGP",),
        ("SIN",),
        ("URS",),
    ]


def test_noc_regions_sgp_copia_dados_de_sin(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT noc, region, notes FROM refined.noc_regions WHERE noc IN ('SGP', 'SIN') ORDER BY noc",
    ) == [("SGP", "Singapore", None), ("SIN", "Singapore", None)]


def test_noc_regions_apara_texto_e_converte_ausencias(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT noc, region, notes FROM refined.noc_regions WHERE noc IN ('BRA', 'ROT', 'URS') ORDER BY noc",
    ) == [
        ("BRA", "Brazil", None),
        ("ROT", None, "Refugee Olympic Team"),
        ("URS", "Russia", "antiga"),
    ]


def test_noc_regions_nao_duplica_sgp_se_a_origem_ja_tiver(con):
    con.execute("INSERT INTO raw.noc_regions VALUES ('SGP', 'Singapore', '')")
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT COUNT(*) FROM refined.noc_regions WHERE noc = 'SGP'"
    ) == [(1,)]


def test_noc_regions_noc_unico_e_nao_nulo(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT COUNT(*), COUNT(DISTINCT noc), COUNT(noc) FROM refined.noc_regions"
    ) == [(5, 5, 5)]


def test_noc_regions_todas_as_colunas_varchar(con):
    refined.executar(con, refined.PASTA_SQL)

    tipos = linhas(
        con,
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'refined' AND table_name = 'noc_regions' ORDER BY ordinal_position",
    )
    assert tipos == [("noc", "VARCHAR"), ("region", "VARCHAR"), ("notes", "VARCHAR")]

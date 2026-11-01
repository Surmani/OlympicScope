"""Testes de pipeline/refined.py e dos SQL de sql/refined/.

Nenhum teste abre data/olympics.duckdb nem lê raw/: o schema raw é
inventado em DuckDB em memória ou em tmp_path. Os SQL testados são os
arquivos reais de sql/refined/.
"""

import duckdb
import pytest

from pipeline import db, refined

COLUNAS_ATHLETE_EVENTS = (
    '"ID", "Name", "Sex", "Age", "Height", "Weight", "Team", "NOC", '
    '"Games", "Year", "Season", "City", "Sport", "Event", "Medal"'
)


def criar_raw_inventado(conexao):
    """Cria o schema raw com dados inventados, tudo VARCHAR como na ingestão.

    athlete_events tem 3 edições: 1956 Summer com duas cidades (como na H2),
    1992 Summer e 1994 Winter (esta com espaços sobrando, para testar o TRIM).
    """
    conexao.execute("CREATE SCHEMA raw")
    conexao.execute(
        "CREATE TABLE raw.noc_regions AS SELECT * FROM (VALUES "
        "('BRA', 'Brazil', ''), "
        "(' URS ', ' Russia ', ' antiga '), "
        "('ROT', 'NA', 'Refugee Olympic Team'), "
        "('SIN', 'Singapore', '')"
        ') AS t("NOC", "region", "notes")'
    )
    conexao.execute(
        "CREATE TABLE raw.athlete_events AS SELECT * FROM (VALUES "
        "('1', 'Ana', 'F', '24', '170', '60', 'Brazil', 'BRA', '1956 Summer', "
        "'1956', 'Summer', 'Melbourne', 'Swimming', 'Swimming 100m', 'Gold'), "
        "('2', 'Bo', 'M', 'NA', 'NA', 'NA', 'Brazil', 'BRA', '1956 Summer', "
        "'1956', 'Summer', 'Stockholm', 'Equestrianism', 'Dressage', 'NA'), "
        "('3', 'Cy', 'M', '30', '180', '80.5', 'Brazil', 'BRA', '1992 Summer', "
        "'1992', 'Summer', 'Barcelona', 'Swimming', 'Swimming 100m', 'NA'), "
        "('1', 'Ana', 'F', '62', '170', '61', 'Brazil', 'BRA', ' 1994 Winter ', "
        "' 1994 ', ' Winter ', ' Lillehammer ', 'Skiing', 'Skiing Slalom', 'NA')"
        f") AS t({COLUNAS_ATHLETE_EVENTS})"
    )


@pytest.fixture
def con():
    conexao = duckdb.connect()
    criar_raw_inventado(conexao)
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
    criar_raw_inventado(conexao)
    conexao.close()
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)

    refined.main()
    primeira = capsys.readouterr().out
    refined.main()
    segunda = capsys.readouterr().out

    assert primeira == segunda
    assert primeira == (
        "refined.noc_regions: 5 linhas\n"
        "refined.games: 3 linhas\n"
        "refined.games_cities: 4 linhas\n"
    )


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


# --- refined.games e refined.games_cities ---------------------------------------


def test_games_uma_linha_por_edicao_mesmo_com_duas_cidades(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(con, "SELECT games_id, year, season FROM refined.games") == [
        ("1956 Summer", 1956, "Summer"),
        ("1992 Summer", 1992, "Summer"),
        ("1994 Winter", 1994, "Winter"),
    ]


def test_games_tipos(con):
    refined.executar(con, refined.PASTA_SQL)

    tipos = linhas(
        con,
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'refined' AND table_name = 'games' ORDER BY ordinal_position",
    )
    assert tipos == [
        ("games_id", "VARCHAR"),
        ("year", "INTEGER"),
        ("season", "VARCHAR"),
    ]


def test_games_verao_e_inverno_do_mesmo_ano_sao_edicoes_distintas(con):
    con.execute(
        "INSERT INTO raw.athlete_events VALUES ('4', 'Di', 'F', '20', '160', '50', "
        "'Brazil', 'BRA', '1992 Winter', '1992', 'Winter', 'Albertville', "
        "'Skiing', 'Skiing Slalom', 'NA')"
    )
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT games_id FROM refined.games WHERE year = 1992 ORDER BY season"
    ) == [("1992 Summer",), ("1992 Winter",)]


def test_games_cities_guarda_todas_as_cidades(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(con, "SELECT games_id, city FROM refined.games_cities") == [
        ("1956 Summer", "Melbourne"),
        ("1956 Summer", "Stockholm"),
        ("1992 Summer", "Barcelona"),
        ("1994 Winter", "Lillehammer"),
    ]


def test_games_cities_toda_edicao_existe_em_games(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT COUNT(*) FROM refined.games_cities AS c "
        "LEFT JOIN refined.games AS g USING (games_id) WHERE g.games_id IS NULL",
    ) == [(0,)]

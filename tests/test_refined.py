"""Testes de pipeline/refined.py e dos SQL de sql/refined/.

Nenhum teste abre data/olympics.duckdb nem lê raw/: o schema raw é
inventado em DuckDB em memória ou em tmp_path. Os SQL testados são os
arquivos reais de sql/refined/.
"""

from decimal import Decimal

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


# --- main --------------------------------------------------------------------
# (os testes do executor genérico ficam em tests/test_executor_sql.py)


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
        "refined.events: 3 linhas\n"
        "refined.athletes: 3 linhas\n"
        "refined.athlete_results: 4 linhas\n"
        "verificações: 12 de 12 ok\n"
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
        "SELECT noc, region, notes FROM refined.noc_regions WHERE noc IN ('SGP', "
        "'SIN') ORDER BY noc",
    ) == [("SGP", "Singapore", None), ("SIN", "Singapore", None)]


def test_noc_regions_apara_texto_e_converte_ausencias(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT noc, region, notes FROM refined.noc_regions WHERE noc IN ('BRA', "
        "'ROT', 'URS') ORDER BY noc",
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
        "WHERE table_schema = 'refined' AND table_name = 'noc_regions' ORDER BY "
        "ordinal_position",
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
        "WHERE table_schema = 'refined' AND table_name = 'games' ORDER BY "
        "ordinal_position",
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


# --- refined.events -------------------------------------------------------------


def test_events_uma_linha_por_prova_com_id_ordenado(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(con, "SELECT event_id, sport, event FROM refined.events") == [
        (1, "Equestrianism", "Dressage"),
        (2, "Skiing", "Skiing Slalom"),
        (3, "Swimming", "Swimming 100m"),
    ]


def test_events_tipos(con):
    refined.executar(con, refined.PASTA_SQL)

    tipos = linhas(
        con,
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'refined' AND table_name = 'events' ORDER BY "
        "ordinal_position",
    )
    assert tipos == [
        ("event_id", "INTEGER"),
        ("sport", "VARCHAR"),
        ("event", "VARCHAR"),
    ]


def test_events_espaco_sobrando_nao_cria_prova_nova(con):
    con.execute(
        "INSERT INTO raw.athlete_events VALUES ('5', 'Ed', 'M', '25', '175', '70', "
        "'Brazil', 'BRA', '1994 Winter', '1994', 'Winter', 'Lillehammer', "
        "' Skiing ', ' Skiing Slalom ', 'NA')"
    )
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(con, "SELECT COUNT(*) FROM refined.events") == [(3,)]


def test_events_id_igual_em_duas_execucoes_e_independe_da_ordem_das_linhas(con):
    refined.executar(con, refined.PASTA_SQL)
    primeira = linhas(con, "SELECT event_id, sport, event FROM refined.events")

    # Mesma entrada em outra ordem física: os ids não podem mudar.
    con.execute(
        "CREATE OR REPLACE TABLE raw.athlete_events AS "
        'SELECT * FROM raw.athlete_events ORDER BY "Event" DESC'
    )
    refined.executar(con, refined.PASTA_SQL)
    segunda = linhas(con, "SELECT event_id, sport, event FROM refined.events")

    assert primeira == segunda


# --- refined.athletes -----------------------------------------------------------


def test_athletes_uma_linha_por_atleta(con):
    refined.executar(con, refined.PASTA_SQL)

    # Ana (ID 1) aparece em duas edições na raw inventada: vira uma linha só.
    assert linhas(con, "SELECT athlete_id, name, sex FROM refined.athletes") == [
        (1, "Ana", "F"),
        (2, "Bo", "M"),
        (3, "Cy", "M"),
    ]


def test_athletes_tipos(con):
    refined.executar(con, refined.PASTA_SQL)

    tipos = linhas(
        con,
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'refined' AND table_name = 'athletes' ORDER BY "
        "ordinal_position",
    )
    assert tipos == [("athlete_id", "INTEGER"), ("name", "VARCHAR"), ("sex", "VARCHAR")]


@pytest.mark.parametrize(
    ("nome_raw", "esperado"),
    [
        ("João   Pedro", "João Pedro"),
        ("João  Pedro", "João Pedro"),
        ("João Pedro", "João Pedro"),
        ("  João Pedro  ", "João Pedro"),
        (" Sergio Ricardo  Reyes, Jr. ", "Sergio Ricardo Reyes, Jr."),
        ("Ana", "Ana"),
    ],
)
def test_athletes_espacos_excedentes_viram_um_espaco_nunca_zero(
    con, nome_raw, esperado
):
    con.execute(
        "INSERT INTO raw.athlete_events VALUES ('9', ?, 'M', '25', '175', '70', "
        "'Brazil', 'BRA', '1992 Summer', '1992', 'Summer', 'Barcelona', "
        "'Swimming', 'Swimming 100m', 'NA')",
        [nome_raw],
    )
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(con, "SELECT name FROM refined.athletes WHERE athlete_id = 9") == [
        (esperado,)
    ]


def test_athletes_homonimos_continuam_separados(con):
    con.execute(
        "INSERT INTO raw.athlete_events VALUES ('7', 'Ana', 'F', '30', '165', '55', "
        "'Brazil', 'BRA', '1992 Summer', '1992', 'Summer', 'Barcelona', "
        "'Swimming', 'Swimming 100m', 'NA')"
    )
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT athlete_id FROM refined.athletes WHERE name = 'Ana' ORDER BY 1"
    ) == [(1,), (7,)]


# --- refined.athlete_results ------------------------------------------------------


def inserir_athlete_event(con, *valores):
    con.execute(
        "INSERT INTO raw.athlete_events VALUES "
        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        list(valores),
    )


# Atleta 8 em 1992 Summer, com as colunas que os testes abaixo variam.
def linha_atleta_8(event="Swimming 100m", medal="NA", weight="70", team="Brazil"):
    return (
        "8",
        "Gil",
        "M",
        "22",
        "180",
        weight,
        team,
        "BRA",
        "1992 Summer",
        "1992",
        "Summer",
        "Barcelona",
        "Swimming",
        event,
        medal,
    )


def test_fato_converte_tipos_e_na_vira_null(con):
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT athlete_id, games_id, noc, team, age, height, weight, medal "
        "FROM refined.athlete_results ORDER BY games_id, athlete_id",
    ) == [
        (1, "1956 Summer", "BRA", "Brazil", 24, 170, Decimal("60.00"), "Gold"),
        (2, "1956 Summer", "BRA", "Brazil", None, None, None, None),
        (3, "1992 Summer", "BRA", "Brazil", 30, 180, Decimal("80.50"), None),
        (1, "1994 Winter", "BRA", "Brazil", 62, 170, Decimal("61.00"), None),
    ]


def test_fato_tipos(con):
    refined.executar(con, refined.PASTA_SQL)

    tipos = linhas(
        con,
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'refined' AND table_name = 'athlete_results' "
        "ORDER BY ordinal_position",
    )
    assert tipos == [
        ("athlete_id", "INTEGER"),
        ("games_id", "VARCHAR"),
        ("event_id", "INTEGER"),
        ("noc", "VARCHAR"),
        ("team", "VARCHAR"),
        ("age", "INTEGER"),
        ("height", "INTEGER"),
        ("weight", "DECIMAL(5,2)"),
        ("medal", "VARCHAR"),
    ]


def test_fato_peso_com_muitas_casas_arredonda_para_duas(con):
    inserir_athlete_event(con, *linha_atleta_8(weight="74.6666666666667"))
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT weight FROM refined.athlete_results WHERE athlete_id = 8"
    ) == [(Decimal("74.67"),)]


def test_fato_linha_identica_sai_ficando_uma(con):
    inserir_athlete_event(con, *linha_atleta_8())
    inserir_athlete_event(con, *linha_atleta_8())
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con, "SELECT COUNT(*) FROM refined.athlete_results WHERE athlete_id = 8"
    ) == [(1,)]


def test_fato_medalhas_em_provas_diferentes_ficam_todas(con):
    # Mesmo atleta, mesma edição, provas diferentes (100 m e 200 m): não é duplicata.
    inserir_athlete_event(con, *linha_atleta_8(event="Swimming 100m", medal="Gold"))
    inserir_athlete_event(con, *linha_atleta_8(event="Swimming 200m", medal="Gold"))
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT e.event, r.medal FROM refined.athlete_results AS r "
        "JOIN refined.events AS e USING (event_id) "
        "WHERE r.athlete_id = 8 ORDER BY e.event",
    ) == [("Swimming 100m", "Gold"), ("Swimming 200m", "Gold")]


def test_fato_mesma_prova_com_medalha_diferente_fica(con):
    # Como em Rowing 1900: mesma prova, uma linha com medalha e outra sem.
    inserir_athlete_event(con, *linha_atleta_8(medal="Bronze"))
    inserir_athlete_event(con, *linha_atleta_8(medal="NA"))
    refined.executar(con, refined.PASTA_SQL)

    assert linhas(
        con,
        "SELECT medal FROM refined.athlete_results WHERE athlete_id = 8 "
        "ORDER BY medal NULLS LAST",
    ) == [("Bronze",), (None,)]


def test_fato_toda_chave_existe_na_dimensao(con):
    refined.executar(con, refined.PASTA_SQL)

    orfaos = linhas(
        con,
        "SELECT "
        "COUNT(*) FILTER (WHERE a.athlete_id IS NULL), "
        "COUNT(*) FILTER (WHERE g.games_id IS NULL), "
        "COUNT(*) FILTER (WHERE e.event_id IS NULL), "
        "COUNT(*) FILTER (WHERE n.noc IS NULL) "
        "FROM refined.athlete_results AS r "
        "LEFT JOIN refined.athletes AS a ON r.athlete_id = a.athlete_id "
        "LEFT JOIN refined.games AS g ON r.games_id = g.games_id "
        "LEFT JOIN refined.events AS e ON r.event_id = e.event_id "
        "LEFT JOIN refined.noc_regions AS n ON r.noc = n.noc",
    )
    assert orfaos == [(0, 0, 0, 0)]


# --- verificações (sql/verificacoes/refined.sql) ---------------------------------


def problemas_por_verificacao(con):
    return dict(refined.verificar(con, refined.ARQUIVO_VERIFICACOES))


def test_verificacoes_dados_consistentes_dao_zero_problemas(con):
    refined.executar(con, refined.PASTA_SQL)
    resultados = refined.verificar(con, refined.ARQUIVO_VERIFICACOES)

    assert len(resultados) == 12
    assert all(problemas == 0 for _, problemas in resultados)


def test_verificacoes_apontam_noc_orfao_na_fato(con):
    # Atleta com um NOC que não existe em noc_regions.
    inserir_athlete_event(
        con,
        "8", "Gil", "M", "22", "180", "70", "Atlantis", "XXX", "1992 Summer",
        "1992", "Summer", "Barcelona", "Swimming", "Swimming 100m", "NA",
    )  # fmt: skip
    refined.executar(con, refined.PASTA_SQL)
    problemas = problemas_por_verificacao(con)

    assert problemas["athlete_results: todo noc existe em noc_regions"] == 1
    assert sum(problemas.values()) == 1


def test_verificacoes_apontam_chave_repetida_na_dimensao(con):
    refined.executar(con, refined.PASTA_SQL)
    con.execute("INSERT INTO refined.games VALUES ('1992 Summer', 1992, 'Summer')")
    problemas = problemas_por_verificacao(con)

    assert problemas["games: games_id único e não nulo"] == 1


def test_verificacoes_apontam_medalha_invalida(con):
    refined.executar(con, refined.PASTA_SQL)
    con.execute(
        "UPDATE refined.athlete_results SET medal = 'Ouro' WHERE athlete_id = 3"
    )
    problemas = problemas_por_verificacao(con)

    assert problemas["athlete_results: medal só Gold, Silver, Bronze ou NULL"] == 1


def test_main_com_orfao_encerra_com_codigo_1(tmp_path, monkeypatch, capsys):
    banco = tmp_path / "teste.duckdb"
    conexao = duckdb.connect(str(banco))
    criar_raw_inventado(conexao)
    inserir_athlete_event(
        conexao,
        "8", "Gil", "M", "22", "180", "70", "Atlantis", "XXX", "1992 Summer",
        "1992", "Summer", "Barcelona", "Swimming", "Swimming 100m", "NA",
    )  # fmt: skip
    conexao.close()
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)

    with pytest.raises(SystemExit) as saida_programa:
        refined.main()

    assert saida_programa.value.code == 1
    saida = capsys.readouterr()
    assert "verificações: 1 de 12 falharam" in saida.err
    assert "athlete_results: todo noc existe em noc_regions: 1 problemas" in saida.err
    assert "ok" not in saida.out

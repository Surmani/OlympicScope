"""Testes dos SQL de sql/marts/ sobre uma refined inventada em memória.

Nenhum teste abre data/olympics.duckdb nem lê raw/. Os SQL executados são os
arquivos reais de sql/marts/, pelo mesmo executor do pipeline.
"""

import duckdb
import pytest

from pipeline import executor_sql, marts


def criar_refined_inventada(conexao):
    """Refined mínima com as colunas que os marts usam.

    2016 Summer:
    - Basquete: BRA campeão com 3 jogadores (1 ouro, 3 registros); USA prata.
    - 100 m: JAM ouro, KEN prata, ARG participa sem medalha.
    - Natação: BRA bronze e CAN bronze (duas medalhas de bronze na prova).
    - Art Competitions: USA ouro (tem que ser ignorado).
    2012 Summer: 100 m com USA ouro, BRA prata, ARG sem medalha.
    2014 Winter: Downhill com CAN ouro, USA prata, BRA sem medalha.
    1906 Summer: KEN ouro nos 100 m (a edição inteira tem que ser ignorada).
    """
    conexao.execute("CREATE SCHEMA refined")
    conexao.execute(
        "CREATE TABLE refined.events AS SELECT * FROM (VALUES "
        "(1, 'Basketball', 'Basketball Men''s Basketball'), "
        "(2, 'Athletics', 'Athletics Men''s 100 metres'), "
        "(3, 'Art Competitions', 'Art Competitions Mixed Painting'), "
        "(4, 'Swimming', 'Swimming Men''s 100 metres Freestyle'), "
        "(5, 'Alpine Skiing', 'Alpine Skiing Men''s Downhill')"
        ") AS t(event_id, sport, event)"
    )
    conexao.execute(
        "CREATE TABLE refined.games AS SELECT * FROM (VALUES "
        "('1906 Summer', 1906, 'Summer'), ('2012 Summer', 2012, 'Summer'), "
        "('2014 Winter', 2014, 'Winter'), ('2016 Summer', 2016, 'Summer')"
        ") AS t(games_id, year, season)"
    )
    conexao.execute(
        "CREATE TABLE refined.noc_regions AS SELECT * FROM (VALUES "
        "('ARG', 'Argentina', NULL), ('BRA', 'Brazil', NULL), "
        "('CAN', 'Canada', NULL), ('JAM', 'Jamaica', NULL), "
        "('KEN', 'Kenya', NULL), ('USA', 'USA', NULL)"
        ") AS t(noc, region, notes)"
    )
    conexao.execute(
        "CREATE TABLE refined.athlete_results AS SELECT * FROM (VALUES "
        "(1, '2016 Summer', 1, 'BRA', 'Gold'), "
        "(2, '2016 Summer', 1, 'BRA', 'Gold'), "
        "(3, '2016 Summer', 1, 'BRA', 'Gold'), "
        "(4, '2016 Summer', 1, 'USA', 'Silver'), "
        "(5, '2016 Summer', 1, 'USA', 'Silver'), "
        "(6, '2016 Summer', 1, 'USA', 'Silver'), "
        "(7, '2016 Summer', 2, 'JAM', 'Gold'), "
        "(8, '2016 Summer', 2, 'KEN', 'Silver'), "
        "(9, '2016 Summer', 2, 'ARG', NULL), "
        "(10, '2016 Summer', 3, 'USA', 'Gold'), "
        "(11, '2016 Summer', 4, 'BRA', 'Bronze'), "
        "(13, '2016 Summer', 4, 'CAN', 'Bronze'), "
        "(20, '2012 Summer', 2, 'USA', 'Gold'), "
        "(21, '2012 Summer', 2, 'BRA', 'Silver'), "
        "(22, '2012 Summer', 2, 'ARG', NULL), "
        "(30, '2014 Winter', 5, 'CAN', 'Gold'), "
        "(31, '2014 Winter', 5, 'USA', 'Silver'), "
        "(32, '2014 Winter', 5, 'BRA', NULL), "
        "(12, '1906 Summer', 2, 'KEN', 'Gold')"
        ") AS t(athlete_id, games_id, event_id, noc, medal)"
    )


@pytest.fixture
def con():
    conexao = duckdb.connect()
    criar_refined_inventada(conexao)
    executor_sql.executar(conexao, marts.PASTA_SQL, "marts")
    yield conexao
    conexao.close()


def linhas(con, sql):
    return con.execute(sql).fetchall()


# --- 01_medalhas_por_pais_edicao --------------------------------------------------


def test_medalhas_por_pais_edicao_quadro_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, games_id, year, season, ouro, prata, bronze, "
        "medalhas_conquistadas, registros_medalhistas, ranking_edicao "
        "FROM marts.medalhas_por_pais_edicao WHERE games_id = '2016 Summer'",
    ) == [
        ("BRA", "Brazil", "2016 Summer", 2016, "Summer", 1, 0, 1, 2, 4, 1),
        ("JAM", "Jamaica", "2016 Summer", 2016, "Summer", 1, 0, 0, 1, 1, 2),
        ("KEN", "Kenya", "2016 Summer", 2016, "Summer", 0, 1, 0, 1, 1, 3),
        ("USA", "USA", "2016 Summer", 2016, "Summer", 0, 1, 0, 1, 3, 3),
        ("CAN", "Canada", "2016 Summer", 2016, "Summer", 0, 0, 1, 1, 1, 5),
        ("ARG", "Argentina", "2016 Summer", 2016, "Summer", 0, 0, 0, 0, 0, None),
    ]


def test_time_de_3_jogadores_conta_1_medalha_e_3_registros(con):
    # Teste previsto na spec (seção "Qualidade e testes"). USA só tem a prata
    # do basquete com 3 jogadores (o ouro em Art Competitions é excluído).
    assert linhas(
        con,
        "SELECT prata, medalhas_conquistadas, registros_medalhistas "
        "FROM marts.medalhas_por_pais_edicao "
        "WHERE noc = 'USA' AND games_id = '2016 Summer'",
    ) == [(1, 1, 3)]


def test_art_competitions_fica_fora(con):
    # Sem a exclusão, USA teria 1 ouro e ficaria em 2º.
    assert linhas(
        con,
        "SELECT ouro FROM marts.medalhas_por_pais_edicao "
        "WHERE noc = 'USA' AND games_id = '2016 Summer'",
    ) == [(0,)]


def test_jogos_de_1906_ficam_fora(con):
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.medalhas_por_pais_edicao "
        "WHERE games_id = '1906 Summer'",
    ) == [(0,)]


def test_empate_divide_a_posicao_e_a_proxima_pula(con):
    assert linhas(
        con,
        "SELECT noc, ranking_edicao FROM marts.medalhas_por_pais_edicao "
        "WHERE games_id = '2016 Summer' AND ranking_edicao IS NOT NULL "
        "ORDER BY ranking_edicao, noc",
    ) == [("BRA", 1), ("JAM", 2), ("KEN", 3), ("USA", 3), ("CAN", 5)]


def test_noc_sem_medalha_aparece_com_zeros_e_sem_ranking(con):
    assert linhas(
        con,
        "SELECT medalhas_conquistadas, registros_medalhistas, ranking_edicao "
        "FROM marts.medalhas_por_pais_edicao "
        "WHERE noc = 'ARG' AND games_id = '2016 Summer'",
    ) == [(0, 0, None)]


def test_grao_noc_por_edicao_sem_repeticao(con):
    assert linhas(
        con,
        "SELECT COUNT(*), COUNT(DISTINCT (noc, games_id)) "
        "FROM marts.medalhas_por_pais_edicao",
    ) == [(12, 12)]


# --- 02_quadro_historico ----------------------------------------------------------


def test_quadro_historico_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, season, ouro, prata, bronze, medalhas_conquistadas, "
        "registros_medalhistas, edicoes_disputadas, ranking_historico "
        "FROM marts.quadro_historico",
    ) == [
        ("BRA", "Brazil", "Summer", 1, 1, 1, 3, 5, 2, 1),
        ("USA", "USA", "Summer", 1, 1, 0, 2, 4, 2, 2),
        ("JAM", "Jamaica", "Summer", 1, 0, 0, 1, 1, 1, 3),
        ("KEN", "Kenya", "Summer", 0, 1, 0, 1, 1, 1, 4),
        ("CAN", "Canada", "Summer", 0, 0, 1, 1, 1, 1, 5),
        ("ARG", "Argentina", "Summer", 0, 0, 0, 0, 0, 2, None),
        ("CAN", "Canada", "Winter", 1, 0, 0, 1, 1, 1, 1),
        ("USA", "USA", "Winter", 0, 1, 0, 1, 1, 1, 2),
        ("BRA", "Brazil", "Winter", 0, 0, 0, 0, 0, 1, None),
    ]


def test_quadro_historico_ranking_separado_por_temporada(con):
    # CAN é 5º no Verão e 1º no Inverno: cada temporada tem o seu quadro.
    assert linhas(
        con,
        "SELECT season, ranking_historico FROM marts.quadro_historico "
        "WHERE noc = 'CAN' ORDER BY season",
    ) == [("Summer", 5), ("Winter", 1)]


def test_quadro_historico_1906_nao_conta_edicao_nem_medalha(con):
    # KEN só tem 2016 válido; o ouro de 1906 não entra.
    assert linhas(
        con,
        "SELECT ouro, edicoes_disputadas FROM marts.quadro_historico WHERE noc = 'KEN'",
    ) == [(0, 1)]


def test_quadro_historico_bate_com_o_mart_01(con):
    assert linhas(
        con,
        "SELECT "
        "(SELECT SUM(medalhas_conquistadas) FROM marts.quadro_historico), "
        "(SELECT SUM(medalhas_conquistadas) FROM marts.medalhas_por_pais_edicao), "
        "(SELECT SUM(registros_medalhistas) FROM marts.quadro_historico), "
        "(SELECT SUM(registros_medalhistas) FROM marts.medalhas_por_pais_edicao), "
        "(SELECT SUM(edicoes_disputadas) FROM marts.quadro_historico), "
        "(SELECT COUNT(*) FROM marts.medalhas_por_pais_edicao)",
    ) == [(10, 10, 14, 14, 12, 12)]

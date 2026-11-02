"""Testes dos SQL de sql/marts/ sobre uma refined inventada em memória.

Nenhum teste abre data/olympics.duckdb nem lê raw/. Os SQL executados são os
arquivos reais de sql/marts/, pelo mesmo executor do pipeline.
"""

from decimal import Decimal
from decimal import Decimal as D

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
    Atleta 10 (USA) só fez Art Competitions em 2016; atleta 11 (BRA) fez duas
    provas em 2016. games_cities: 2016 com duas cidades (como 1956 na H2).
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
        "CREATE TABLE refined.games_cities AS SELECT * FROM (VALUES "
        "('1906 Summer', 'Athina'), ('2012 Summer', 'London'), "
        "('2014 Winter', 'Sochi'), ('2016 Summer', 'Rio de Janeiro'), "
        "('2016 Summer', 'Belo Horizonte')"
        ") AS t(games_id, city)"
    )
    conexao.execute(
        "CREATE TABLE refined.noc_regions AS SELECT * FROM (VALUES "
        "('ARG', 'Argentina', NULL), ('BRA', 'Brazil', NULL), "
        "('CAN', 'Canada', NULL), ('JAM', 'Jamaica', NULL), "
        "('KEN', 'Kenya', NULL), ('USA', 'USA', NULL)"
        ") AS t(noc, region, notes)"
    )
    # Sexo: 2016 tem 7 M e 4 F válidos (o atleta 10, F, só fez Art);
    # 2012 só tem homens (como 1896); 2014 tem 2 F e 1 M.
    conexao.execute(
        "CREATE TABLE refined.athletes AS SELECT * FROM (VALUES "
        "(1, 'A1', 'M'), (2, 'A2', 'M'), (3, 'A3', 'M'), (4, 'A4', 'M'), "
        "(5, 'A5', 'M'), (6, 'A6', 'M'), (7, 'A7', 'F'), (8, 'A8', 'F'), "
        "(9, 'A9', 'M'), (10, 'A10', 'F'), (11, 'A11', 'F'), (12, 'A12', 'M'), "
        "(13, 'A13', 'F'), (20, 'A20', 'M'), (21, 'A21', 'M'), (22, 'A22', 'M'), "
        "(30, 'A30', 'F'), (31, 'A31', 'M'), (32, 'A32', 'F')"
        ") AS t(athlete_id, name, sex)"
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
        "(11, '2016 Summer', 2, 'BRA', NULL), "
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
    # Idade, altura (cm) e peso (kg) por atleta, iguais em todas as provas da
    # mesma edição, como nos dados reais. Atletas 3 e 22 sem altura e peso.
    conexao.execute(
        "ALTER TABLE refined.athlete_results ADD COLUMN age INTEGER; "
        "ALTER TABLE refined.athlete_results ADD COLUMN height INTEGER; "
        "ALTER TABLE refined.athlete_results ADD COLUMN weight DECIMAL(5, 2)"
    )
    conexao.execute(
        "UPDATE refined.athlete_results AS r SET age = v.age, height = v.height, "
        "weight = v.weight FROM (VALUES "
        "(1, 20, 200, 100), (2, 22, 210, 110), (3, 24, NULL, NULL), "
        "(4, 25, 190, 90), (5, 27, 200, 100), (6, 29, 210, 110), "
        "(7, 22, 170, 60), (8, 24, 160, 50), (9, 30, 180, 75), "
        "(10, 40, 165, 55), (11, 19, 175, 65), (12, 26, 178, 70), "
        "(13, 21, 165, 55), (20, 23, 180, 75), (21, 25, 182, 77), "
        "(22, 27, NULL, NULL), (30, 24, 168, 62), (31, 28, 185, 85), "
        "(32, 26, 166, 60)"
        ") AS v(athlete_id, age, height, weight) "
        "WHERE r.athlete_id = v.athlete_id"
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


# --- 03_evolucao_olimpica ---------------------------------------------------------


def test_evolucao_olimpica_completa(con):
    assert linhas(
        con,
        "SELECT games_id, year, season, city, atletas, paises, modalidades, provas "
        "FROM marts.evolucao_olimpica",
    ) == [
        ("2012 Summer", 2012, "Summer", "London", 3, 3, 1, 1),
        ("2014 Winter", 2014, "Winter", "Sochi", 3, 3, 1, 1),
        ("2016 Summer", 2016, "Summer", "Belo Horizonte | Rio de Janeiro", 11, 6, 3, 3),
    ]


def test_evolucao_atleta_em_duas_provas_conta_uma_vez(con):
    # Atleta 11 fez natação e 100 m em 2016; 12 linhas válidas, 11 atletas.
    assert linhas(
        con,
        "SELECT atletas FROM marts.evolucao_olimpica WHERE games_id = '2016 Summer'",
    ) == [(11,)]


def test_evolucao_art_competitions_fora_das_contagens(con):
    # Sem a exclusão: 12 atletas (o 10 só fez Art), 4 modalidades, 4 provas.
    assert linhas(
        con,
        "SELECT atletas, modalidades, provas FROM marts.evolucao_olimpica "
        "WHERE games_id = '2016 Summer'",
    ) == [(11, 3, 3)]


def test_evolucao_1906_fica_fora(con):
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.evolucao_olimpica WHERE games_id = '1906 Summer'",
    ) == [(0,)]


# --- 04_participacao_genero -------------------------------------------------------


def test_participacao_genero_completa(con):
    assert linhas(
        con,
        "SELECT games_id, year, season, sex, atletas, percentual_atletas "
        "FROM marts.participacao_genero",
    ) == [
        ("2012 Summer", 2012, "Summer", "F", 0, Decimal("0.00")),
        ("2012 Summer", 2012, "Summer", "M", 3, Decimal("100.00")),
        ("2014 Winter", 2014, "Winter", "F", 2, Decimal("66.67")),
        ("2014 Winter", 2014, "Winter", "M", 1, Decimal("33.33")),
        ("2016 Summer", 2016, "Summer", "F", 4, Decimal("36.36")),
        ("2016 Summer", 2016, "Summer", "M", 7, Decimal("63.64")),
    ]


def test_participacao_edicao_so_com_homens_tem_linha_f_com_zero(con):
    # Como 1896 nos dados reais: a linha F existe, com 0 atletas e 0%.
    assert linhas(
        con,
        "SELECT atletas, percentual_atletas FROM marts.participacao_genero "
        "WHERE games_id = '2012 Summer' AND sex = 'F'",
    ) == [(0, Decimal("0.00"))]


def test_participacao_art_competitions_e_1906_ficam_fora(con):
    # Sem a exclusão, 2016 teria 5 mulheres (a atleta 10 só fez Art).
    assert linhas(
        con,
        "SELECT atletas FROM marts.participacao_genero "
        "WHERE games_id = '2016 Summer' AND sex = 'F'",
    ) == [(4,)]
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.participacao_genero WHERE games_id = '1906 Summer'",
    ) == [(0,)]


def test_participacao_bate_com_atletas_do_mart_03(con):
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.evolucao_olimpica AS e "
        "JOIN (SELECT games_id, SUM(atletas) AS total "
        "FROM marts.participacao_genero GROUP BY games_id) AS p USING (games_id) "
        "WHERE e.atletas <> p.total",
    ) == [(0,)]


# --- 05_desempenho_esportivo ------------------------------------------------------


def test_desempenho_esportivo_completo(con):
    assert linhas(
        con,
        "SELECT sport, season, participacoes, atletas, provas, "
        "medalhas_conquistadas, registros_medalhistas "
        "FROM marts.desempenho_esportivo",
    ) == [
        ("Athletics", "Summer", 7, 7, 1, 4, 4),
        ("Basketball", "Summer", 6, 6, 1, 2, 6),
        ("Swimming", "Summer", 2, 2, 1, 2, 2),
        ("Alpine Skiing", "Winter", 3, 3, 1, 2, 2),
    ]


def test_desempenho_basquete_1_medalha_por_time_e_registros_por_jogador(con):
    # Ouro do BRA e prata do USA, times de 3: 2 medalhas e 6 registros.
    assert linhas(
        con,
        "SELECT medalhas_conquistadas, registros_medalhistas "
        "FROM marts.desempenho_esportivo WHERE sport = 'Basketball'",
    ) == [(2, 6)]


def test_desempenho_art_competitions_e_1906_ficam_fora(con):
    # Art não aparece; o ouro do KEN em 1906 não entra no atletismo.
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.desempenho_esportivo "
        "WHERE sport = 'Art Competitions'",
    ) == [(0,)]
    assert linhas(
        con,
        "SELECT participacoes, medalhas_conquistadas FROM marts.desempenho_esportivo "
        "WHERE sport = 'Athletics'",
    ) == [(7, 4)]


# --- 06_perfil_atletas ----------------------------------------------------------


def test_perfil_atletas_completo(con):
    assert linhas(
        con,
        "SELECT sport, sex, season, idade_media, altura_media, peso_media, "
        "n_idade, n_altura, n_peso FROM marts.perfil_atletas",
    ) == [
        ("Athletics", "F", "Summer", D("21.67"), D("168.33"), D("58.33"), 3, 3, 3),
        ("Athletics", "M", "Summer", D("26.25"), D("180.67"), D("75.67"), 4, 3, 3),
        ("Basketball", "M", "Summer", D("24.50"), D("202.00"), D("102.00"), 6, 5, 5),
        ("Swimming", "F", "Summer", D("20.00"), D("170.00"), D("60.00"), 2, 2, 2),
        ("Alpine Skiing", "F", "Winter", D("25.00"), D("167.00"), D("61.00"), 2, 2, 2),
        ("Alpine Skiing", "M", "Winter", D("28.00"), D("185.00"), D("85.00"), 1, 1, 1),
    ]


def test_perfil_atleta_com_varias_provas_entra_uma_vez(con):
    # A atleta 7 ganha uma segunda prova de atletismo em 2016: a média e o n
    # do atletismo feminino não podem mudar.
    con.execute(
        "INSERT INTO refined.events VALUES (6, 'Athletics', 'Athletics Women''s 200 metres')"
    )
    con.execute(
        "INSERT INTO refined.athlete_results "
        "VALUES (7, '2016 Summer', 6, 'JAM', NULL, 22, 170, 60)"
    )
    executor_sql.executar(con, marts.PASTA_SQL, "marts")

    assert linhas(
        con,
        "SELECT idade_media, n_idade FROM marts.perfil_atletas "
        "WHERE sport = 'Athletics' AND sex = 'F'",
    ) == [(D("21.67"), 3)]


def test_perfil_ausencia_nao_entra_na_media_nem_no_n(con):
    # Atleta 3 do basquete sem altura e peso: conta na idade (6) e não na
    # altura e no peso (5).
    assert linhas(
        con,
        "SELECT n_idade, n_altura, n_peso FROM marts.perfil_atletas "
        "WHERE sport = 'Basketball'",
    ) == [(6, 5, 5)]


# --- 07_perfil_atletas_pais -------------------------------------------------------


def test_perfil_atletas_pais_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, sex, season, idade_media, altura_media, peso_media, "
        "n_idade, n_altura, n_peso FROM marts.perfil_atletas_pais",
    ) == [
        (
            "ARG",
            "Argentina",
            "M",
            "Summer",
            D("28.50"),
            D("180.00"),
            D("75.00"),
            2,
            1,
            1,
        ),
        ("BRA", "Brazil", "F", "Summer", D("19.00"), D("175.00"), D("65.00"), 1, 1, 1),
        ("BRA", "Brazil", "M", "Summer", D("22.75"), D("197.33"), D("95.67"), 4, 3, 3),
        ("CAN", "Canada", "F", "Summer", D("21.00"), D("165.00"), D("55.00"), 1, 1, 1),
        ("JAM", "Jamaica", "F", "Summer", D("22.00"), D("170.00"), D("60.00"), 1, 1, 1),
        ("KEN", "Kenya", "F", "Summer", D("24.00"), D("160.00"), D("50.00"), 1, 1, 1),
        ("USA", "USA", "M", "Summer", D("26.00"), D("195.00"), D("93.75"), 4, 4, 4),
        ("BRA", "Brazil", "F", "Winter", D("26.00"), D("166.00"), D("60.00"), 1, 1, 1),
        ("CAN", "Canada", "F", "Winter", D("24.00"), D("168.00"), D("62.00"), 1, 1, 1),
        ("USA", "USA", "M", "Winter", D("28.00"), D("185.00"), D("85.00"), 1, 1, 1),
    ]


def test_perfil_pais_atleta_em_duas_provas_da_mesma_edicao_entra_uma_vez(con):
    # Atleta 11 (BRA, F) fez natação e 100 m em 2016: n = 1, não 2.
    assert linhas(
        con,
        "SELECT n_idade FROM marts.perfil_atletas_pais "
        "WHERE noc = 'BRA' AND sex = 'F' AND season = 'Summer'",
    ) == [(1,)]


def test_perfil_pais_exclusoes(con):
    # USA F só teve a atleta 10, de Art Competitions; KEN M só teve 1906.
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.perfil_atletas_pais "
        "WHERE (noc = 'USA' AND sex = 'F') OR (noc = 'KEN' AND sex = 'M')",
    ) == [(0,)]


def inserir_resultado(con, athlete_id, games_id, event_id, noc, medal):
    """Acrescenta uma participação na refined inventada e refaz os marts."""
    con.execute(
        "INSERT INTO refined.athlete_results VALUES (?, ?, ?, ?, ?, 25, 180, 75)",
        [athlete_id, games_id, event_id, noc, medal],
    )
    executor_sql.executar(con, marts.PASTA_SQL, "marts")


# --- 08_ranking_atletas -----------------------------------------------------------


def test_ranking_atletas_completo(con):
    assert linhas(
        con,
        "SELECT athlete_id, name, sex, noc, ouro, prata, bronze, total_medalhas, "
        "edicoes, ranking FROM marts.ranking_atletas",
    ) == [
        (1, "A1", "M", "BRA", 1, 0, 0, 1, 1, 1),
        (2, "A2", "M", "BRA", 1, 0, 0, 1, 1, 1),
        (3, "A3", "M", "BRA", 1, 0, 0, 1, 1, 1),
        (7, "A7", "F", "JAM", 1, 0, 0, 1, 1, 1),
        (20, "A20", "M", "USA", 1, 0, 0, 1, 1, 1),
        (30, "A30", "F", "CAN", 1, 0, 0, 1, 1, 1),
        (4, "A4", "M", "USA", 0, 1, 0, 1, 1, 7),
        (5, "A5", "M", "USA", 0, 1, 0, 1, 1, 7),
        (6, "A6", "M", "USA", 0, 1, 0, 1, 1, 7),
        (8, "A8", "F", "KEN", 0, 1, 0, 1, 1, 7),
        (21, "A21", "M", "BRA", 0, 1, 0, 1, 1, 7),
        (31, "A31", "M", "USA", 0, 1, 0, 1, 1, 7),
        (11, "A11", "F", "BRA", 0, 0, 1, 1, 1, 13),
        (13, "A13", "F", "CAN", 0, 0, 1, 1, 1, 13),
    ]


def test_ranking_so_medalhistas_e_sem_exclusoes(con):
    # 9, 22 e 32 nunca ganharam medalha; 10 só em Art; 12 só em 1906.
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.ranking_atletas "
        "WHERE athlete_id IN (9, 22, 32, 10, 12)",
    ) == [(0,)]


def test_ranking_cada_jogador_do_time_tem_sua_medalha(con):
    # Os 3 jogadores do basquete do BRA têm 1 ouro cada.
    assert linhas(
        con, "SELECT SUM(ouro) FROM marts.ranking_atletas WHERE athlete_id IN (1, 2, 3)"
    ) == [(3,)]


def test_ranking_atleta_com_dois_paises_e_duas_edicoes(con):
    # Atleta 4 (prata pelo USA em 2016) ganha ouro pelo CAN em 2012.
    inserir_resultado(con, 4, "2012 Summer", 2, "CAN", "Gold")

    assert linhas(
        con,
        "SELECT noc, ouro, prata, total_medalhas, edicoes, ranking "
        "FROM marts.ranking_atletas WHERE athlete_id = 4",
    ) == [("CAN | USA", 1, 1, 2, 2, 1)]


# --- 09_estreias_paises -----------------------------------------------------------


def test_estreias_paises_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, season, primeira_edicao, ano_primeira_edicao, "
        "primeira_medalha, ano_primeira_medalha, edicoes_ate_primeira_medalha, "
        "primeiro_ouro, ano_primeiro_ouro FROM marts.estreias_paises",
    ) == [
        ("ARG", "Argentina", "Summer", "2012 Summer", 2012, None, None, None, None, None),
        ("BRA", "Brazil", "Summer", "2012 Summer", 2012, "2012 Summer", 2012, 1,
         "2016 Summer", 2016),
        ("USA", "USA", "Summer", "2012 Summer", 2012, "2012 Summer", 2012, 1,
         "2012 Summer", 2012),
        ("CAN", "Canada", "Summer", "2016 Summer", 2016, "2016 Summer", 2016, 1,
         None, None),
        ("JAM", "Jamaica", "Summer", "2016 Summer", 2016, "2016 Summer", 2016, 1,
         "2016 Summer", 2016),
        ("KEN", "Kenya", "Summer", "2016 Summer", 2016, "2016 Summer", 2016, 1,
         None, None),
        ("BRA", "Brazil", "Winter", "2014 Winter", 2014, None, None, None, None, None),
        ("CAN", "Canada", "Winter", "2014 Winter", 2014, "2014 Winter", 2014, 1,
         "2014 Winter", 2014),
        ("USA", "USA", "Winter", "2014 Winter", 2014, "2014 Winter", 2014, 1,
         None, None),
    ]  # fmt: skip


def test_estreias_primeira_medalha_na_segunda_edicao(con):
    # ARG estreou em 2012 sem medalha e ganha bronze em 2016: 2 edições até
    # a primeira medalha.
    inserir_resultado(con, 9, "2016 Summer", 4, "ARG", "Bronze")

    assert linhas(
        con,
        "SELECT primeira_medalha, edicoes_ate_primeira_medalha, primeiro_ouro "
        "FROM marts.estreias_paises WHERE noc = 'ARG'",
    ) == [("2016 Summer", 2, None)]


def test_estreias_ouro_de_1906_nao_conta(con):
    # KEN tem ouro só em 1906: estreia em 2016 e sem primeiro ouro.
    assert linhas(
        con,
        "SELECT primeira_edicao, primeiro_ouro FROM marts.estreias_paises "
        "WHERE noc = 'KEN'",
    ) == [("2016 Summer", None)]


# --- 10_eficiencia_paises ---------------------------------------------------------


def test_eficiencia_paises_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, games_id, year, season, atletas, medalhas_conquistadas, "
        "medalhas_por_100_atletas FROM marts.eficiencia_paises",
    ) == [
        ("ARG", "Argentina", "2012 Summer", 2012, "Summer", 1, 0, D("0.00")),
        ("BRA", "Brazil", "2012 Summer", 2012, "Summer", 1, 1, D("100.00")),
        ("USA", "USA", "2012 Summer", 2012, "Summer", 1, 1, D("100.00")),
        ("BRA", "Brazil", "2014 Winter", 2014, "Winter", 1, 0, D("0.00")),
        ("CAN", "Canada", "2014 Winter", 2014, "Winter", 1, 1, D("100.00")),
        ("USA", "USA", "2014 Winter", 2014, "Winter", 1, 1, D("100.00")),
        ("ARG", "Argentina", "2016 Summer", 2016, "Summer", 1, 0, D("0.00")),
        ("BRA", "Brazil", "2016 Summer", 2016, "Summer", 4, 2, D("50.00")),
        ("CAN", "Canada", "2016 Summer", 2016, "Summer", 1, 1, D("100.00")),
        ("JAM", "Jamaica", "2016 Summer", 2016, "Summer", 1, 1, D("100.00")),
        ("KEN", "Kenya", "2016 Summer", 2016, "Summer", 1, 1, D("100.00")),
        ("USA", "USA", "2016 Summer", 2016, "Summer", 3, 1, D("33.33")),
    ]


def test_eficiencia_delegacao_conta_cada_atleta_uma_vez_e_sem_art(con):
    # BRA 2016: atletas 1, 2, 3 e 11 (o 11 em duas provas) = 4.
    # USA 2016: atletas 4, 5 e 6; a 10, só de Art Competitions, não conta.
    assert linhas(
        con,
        "SELECT noc, atletas FROM marts.eficiencia_paises "
        "WHERE games_id = '2016 Summer' AND noc IN ('BRA', 'USA') ORDER BY noc",
    ) == [("BRA", 4), ("USA", 3)]


# --- 11_dominio_modalidade --------------------------------------------------------


def test_dominio_modalidade_completo(con):
    assert linhas(
        con,
        "SELECT sport, season, noc, region, ouro, prata, bronze, "
        "medalhas_conquistadas, percentual_medalhas, ranking_modalidade "
        "FROM marts.dominio_modalidade",
    ) == [
        ("Athletics", "Summer", "JAM", "Jamaica", 1, 0, 0, 1, D("25.00"), 1),
        ("Athletics", "Summer", "USA", "USA", 1, 0, 0, 1, D("25.00"), 1),
        ("Athletics", "Summer", "BRA", "Brazil", 0, 1, 0, 1, D("25.00"), 3),
        ("Athletics", "Summer", "KEN", "Kenya", 0, 1, 0, 1, D("25.00"), 3),
        ("Basketball", "Summer", "BRA", "Brazil", 1, 0, 0, 1, D("50.00"), 1),
        ("Basketball", "Summer", "USA", "USA", 0, 1, 0, 1, D("50.00"), 2),
        ("Swimming", "Summer", "BRA", "Brazil", 0, 0, 1, 1, D("50.00"), 1),
        ("Swimming", "Summer", "CAN", "Canada", 0, 0, 1, 1, D("50.00"), 1),
        ("Alpine Skiing", "Winter", "CAN", "Canada", 1, 0, 0, 1, D("50.00"), 1),
        ("Alpine Skiing", "Winter", "USA", "USA", 0, 1, 0, 1, D("50.00"), 2),
    ]


def test_dominio_prova_em_grupo_conta_1_medalha_para_o_pais(con):
    # Basquete: 3 jogadores do BRA com ouro = 1 medalha do BRA.
    assert linhas(
        con,
        "SELECT ouro, medalhas_conquistadas FROM marts.dominio_modalidade "
        "WHERE sport = 'Basketball' AND noc = 'BRA'",
    ) == [(1, 1)]


def test_dominio_so_quem_ganhou_e_sem_exclusoes(con):
    # ARG nunca ganhou; Art e o ouro do KEN em 1906 não entram.
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.dominio_modalidade "
        "WHERE noc = 'ARG' OR sport = 'Art Competitions' "
        "OR (noc = 'KEN' AND ouro > 0)",
    ) == [(0,)]


def test_dominio_percentual_soma_100_por_modalidade(con):
    assert linhas(
        con,
        "SELECT sport, SUM(percentual_medalhas) FROM marts.dominio_modalidade "
        "GROUP BY sport ORDER BY sport",
    ) == [
        ("Alpine Skiing", D("100.00")),
        ("Athletics", D("100.00")),
        ("Basketball", D("100.00")),
        ("Swimming", D("100.00")),
    ]


# --- 12_genero_por_pais -----------------------------------------------------------


def test_genero_por_pais_completo(con):
    assert linhas(
        con,
        "SELECT noc, region, games_id, year, season, atletas_f, atletas_m, atletas, "
        "percentual_mulheres FROM marts.genero_por_pais",
    ) == [
        ("ARG", "Argentina", "2012 Summer", 2012, "Summer", 0, 1, 1, D("0.00")),
        ("BRA", "Brazil", "2012 Summer", 2012, "Summer", 0, 1, 1, D("0.00")),
        ("USA", "USA", "2012 Summer", 2012, "Summer", 0, 1, 1, D("0.00")),
        ("BRA", "Brazil", "2014 Winter", 2014, "Winter", 1, 0, 1, D("100.00")),
        ("CAN", "Canada", "2014 Winter", 2014, "Winter", 1, 0, 1, D("100.00")),
        ("USA", "USA", "2014 Winter", 2014, "Winter", 0, 1, 1, D("0.00")),
        ("ARG", "Argentina", "2016 Summer", 2016, "Summer", 0, 1, 1, D("0.00")),
        ("BRA", "Brazil", "2016 Summer", 2016, "Summer", 1, 3, 4, D("25.00")),
        ("CAN", "Canada", "2016 Summer", 2016, "Summer", 1, 0, 1, D("100.00")),
        ("JAM", "Jamaica", "2016 Summer", 2016, "Summer", 1, 0, 1, D("100.00")),
        ("KEN", "Kenya", "2016 Summer", 2016, "Summer", 1, 0, 1, D("100.00")),
        ("USA", "USA", "2016 Summer", 2016, "Summer", 0, 3, 3, D("0.00")),
    ]


def test_genero_por_pais_art_fora_e_atleta_em_duas_provas_conta_uma_vez(con):
    # USA 2016: a atleta 10 (F) só fez Art -> 0 mulheres.
    # BRA 2016: a atleta 11 fez duas provas -> 1 mulher, não 2.
    assert linhas(
        con,
        "SELECT noc, atletas_f FROM marts.genero_por_pais "
        "WHERE games_id = '2016 Summer' AND noc IN ('BRA', 'USA') ORDER BY noc",
    ) == [("BRA", 1), ("USA", 0)]


# --- 13_longevidade_atletas -------------------------------------------------------


def test_longevidade_sem_atleta_com_2_edicoes_fica_vazio(con):
    # Na refined inventada básica, todo atleta disputou uma edição só.
    assert linhas(con, "SELECT COUNT(*) FROM marts.longevidade_atletas") == [(0,)]


def test_longevidade_completo(con):
    inserir_resultado(con, 9, "2012 Summer", 2, "ARG", None)  # 2012 e 2016
    inserir_resultado(con, 31, "2016 Summer", 2, "CAN", None)  # Inverno e Verão
    inserir_resultado(con, 21, "2014 Winter", 5, "BRA", None)  # 2012, 2014, 2016
    inserir_resultado(con, 21, "2016 Summer", 2, "BRA", None)

    assert linhas(
        con,
        "SELECT athlete_id, name, sex, noc, edicoes, primeiro_ano, ultimo_ano, "
        "anos_de_carreira, ranking FROM marts.longevidade_atletas",
    ) == [
        (21, "A21", "M", "BRA", 3, 2012, 2016, 4, 1),
        (9, "A9", "M", "ARG", 2, 2012, 2016, 4, 2),
        (31, "A31", "M", "CAN | USA", 2, 2014, 2016, 2, 3),
    ]


def test_longevidade_1906_e_art_nao_contam_como_edicao(con):
    # Atleta 12 (só 1906) ganha uma participação em 2016; a 10 (só Art) ganha
    # outra prova de Art em 2012. Nenhum dos dois chega a 2 edições válidas.
    inserir_resultado(con, 12, "2016 Summer", 2, "KEN", None)
    inserir_resultado(con, 10, "2012 Summer", 3, "USA", None)

    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.longevidade_atletas WHERE athlete_id IN (10, 12)",
    ) == [(0,)]


# --- 14_medalhistas_extremos ------------------------------------------------------


def test_medalhistas_extremos_completo(con):
    atletismo = "Athletics Men's 100 metres"
    basquete = "Basketball Men's Basketball"
    natacao = "Swimming Men's 100 metres Freestyle"
    esqui = "Alpine Skiing Men's Downhill"
    assert linhas(
        con,
        "SELECT sport, season, extremo, idade, athlete_id, name, sex, noc, games_id, "
        "medalhas, provas FROM marts.medalhistas_extremos",
    ) == [
        ("Athletics", "Summer", "mais jovem", 22, 7, "A7", "F", "JAM", "2016 Summer", 1, atletismo),
        ("Athletics", "Summer", "mais velho", 25, 21, "A21", "M", "BRA", "2012 Summer", 1, atletismo),
        ("Basketball", "Summer", "mais jovem", 20, 1, "A1", "M", "BRA", "2016 Summer", 1, basquete),
        ("Basketball", "Summer", "mais velho", 29, 6, "A6", "M", "USA", "2016 Summer", 1, basquete),
        ("Swimming", "Summer", "mais jovem", 19, 11, "A11", "F", "BRA", "2016 Summer", 1, natacao),
        ("Swimming", "Summer", "mais velho", 21, 13, "A13", "F", "CAN", "2016 Summer", 1, natacao),
        ("Alpine Skiing", "Winter", "mais jovem", 24, 30, "A30", "F", "CAN", "2014 Winter", 1, esqui),
        ("Alpine Skiing", "Winter", "mais velho", 28, 31, "A31", "M", "USA", "2014 Winter", 1, esqui),
    ]  # fmt: skip


def test_extremos_empate_mantem_todos(con):
    # O atleta 9 ganha ouro no atletismo com 25 anos (inserir_resultado usa 25),
    # empatando com o atleta 21 como mais velho.
    inserir_resultado(con, 9, "2016 Summer", 2, "ARG", "Gold")

    assert linhas(
        con,
        "SELECT athlete_id, idade FROM marts.medalhistas_extremos "
        "WHERE sport = 'Athletics' AND extremo = 'mais velho' ORDER BY athlete_id",
    ) == [(9, 25), (21, 25)]


def test_extremos_atleta_com_duas_medalhas_na_mesma_idade_e_uma_linha(con):
    con.execute(
        "INSERT INTO refined.events VALUES (6, 'Swimming', 'Swimming Women''s 200 metres')"
    )
    con.execute(
        "INSERT INTO refined.athlete_results "
        "VALUES (11, '2016 Summer', 6, 'BRA', 'Gold', 19, 175, 65)"
    )
    executor_sql.executar(con, marts.PASTA_SQL, "marts")

    assert linhas(
        con,
        "SELECT athlete_id, medalhas, provas FROM marts.medalhistas_extremos "
        "WHERE sport = 'Swimming' AND extremo = 'mais jovem'",
    ) == [(11, 2, "Swimming Men's 100 metres Freestyle | Swimming Women's 200 metres")]


def test_extremos_exclusoes(con):
    # A atleta 10 (40 anos, ouro só em Art) e o atleta 12 (só 1906) não entram.
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.medalhistas_extremos WHERE athlete_id IN (10, 12)",
    ) == [(0,)]


# --- 15_programa_olimpico ---------------------------------------------------------


def test_programa_olimpico_completo(con):
    assert linhas(
        con,
        "SELECT sport, season, primeira_edicao, primeiro_ano, ultima_edicao, "
        "ultimo_ano, edicoes, ausencias, no_programa_atual "
        "FROM marts.programa_olimpico",
    ) == [
        ("Athletics", "Summer", "2012 Summer", 2012, "2016 Summer", 2016, 2, 0, True),
        ("Basketball", "Summer", "2016 Summer", 2016, "2016 Summer", 2016, 1, 0, True),
        ("Swimming", "Summer", "2016 Summer", 2016, "2016 Summer", 2016, 1, 0, True),
        (
            "Alpine Skiing",
            "Winter",
            "2014 Winter",
            2014,
            "2014 Winter",
            2014,
            1,
            0,
            True,
        ),
    ]


def test_programa_ausencia_e_modalidade_que_saiu(con):
    # 2008 Summer: basquete (volta em 2016, pulando 2012) e beisebol (só 2008).
    con.execute("INSERT INTO refined.games VALUES ('2008 Summer', 2008, 'Summer')")
    con.execute(
        "INSERT INTO refined.events VALUES (7, 'Baseball', 'Baseball Men''s Baseball')"
    )
    con.execute(
        "INSERT INTO refined.athlete_results VALUES "
        "(40, '2008 Summer', 1, 'USA', NULL, 25, 190, 90), "
        "(41, '2008 Summer', 7, 'USA', NULL, 25, 185, 85)"
    )
    executor_sql.executar(con, marts.PASTA_SQL, "marts")

    assert linhas(
        con,
        "SELECT sport, edicoes, ausencias, no_programa_atual FROM marts.programa_olimpico "
        "WHERE sport IN ('Basketball', 'Baseball') ORDER BY sport",
    ) == [("Baseball", 1, 0, False), ("Basketball", 2, 1, True)]


def test_programa_1906_e_art_ficam_fora(con):
    assert linhas(
        con,
        "SELECT COUNT(*) FROM marts.programa_olimpico "
        "WHERE sport = 'Art Competitions' OR primeira_edicao = '1906 Summer'",
    ) == [(0,)]

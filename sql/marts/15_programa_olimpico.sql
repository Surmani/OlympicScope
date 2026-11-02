-- =============================================================================
-- marts.programa_olimpico — unidade 4.3 (mart 15)
-- =============================================================================
--
-- Pergunta: quando cada modalidade entrou e saiu dos Jogos, e quantas vezes
-- ficou de fora?
--
-- Período: Verão de 1896 a 2016 e Inverno de 1924 a 2014 (só os CSVs de
-- origem). "Programa atual" quer dizer a ÚLTIMA EDIÇÃO DO DATASET (2016 no
-- Verão, 2014 no Inverno), não as edições mais recentes dos Jogos.
--
-- Grão: modalidade × temporada.
--
-- Origem: refined (athlete_results, events, games).
--
-- Colunas:
-- - primeira_edicao / primeiro_ano e ultima_edicao / ultimo_ano: primeira e
--   última edição em que a modalidade teve participações.
-- - edicoes: em quantas edições da temporada ela foi disputada.
-- - ausencias: edições da temporada entre a primeira e a última que
--   aconteceram sem ela (> 0 = saiu e voltou).
-- - no_programa_atual: TRUE se estava na última edição da temporada no
--   dataset (2016 ou 2014).
-- - O calendário de edições de cada temporada vem de refined.games, sem 1906.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions não
-- aparece; os Jogos de 1906 não contam como edição.
-- =============================================================================

CREATE OR REPLACE TABLE marts.programa_olimpico AS
WITH disputas AS (
    -- Uma linha por modalidade × edição em que ela foi disputada.
    SELECT DISTINCT e.sport, g.season, g.games_id, g.year
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
calendario AS (
    SELECT season, year
    FROM refined.games
    WHERE games_id <> '1906 Summer'
),
por_modalidade AS (
    SELECT
        sport,
        season,
        ARG_MIN(games_id, year) AS primeira_edicao,
        MIN(year) AS primeiro_ano,
        ARG_MAX(games_id, year) AS ultima_edicao,
        MAX(year) AS ultimo_ano,
        COUNT(*) AS edicoes
    FROM disputas
    GROUP BY sport, season
)
SELECT
    p.sport,
    p.season,
    p.primeira_edicao,
    p.primeiro_ano,
    p.ultima_edicao,
    p.ultimo_ano,
    p.edicoes,
    (
        SELECT COUNT(*)
        FROM calendario AS c
        WHERE c.season = p.season AND c.year BETWEEN p.primeiro_ano AND p.ultimo_ano
    ) - p.edicoes AS ausencias,
    p.ultimo_ano = (
        SELECT MAX(c.year) FROM calendario AS c WHERE c.season = p.season
    ) AS no_programa_atual
FROM por_modalidade AS p
ORDER BY p.season, p.primeiro_ano, p.sport;

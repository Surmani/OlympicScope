-- =============================================================================
-- refined.games — unidade 3.2b
-- =============================================================================
--
-- Grão: uma linha por edição dos Jogos (ex.: '1992 Summer').
-- Origem: raw.athlete_events (271.116 linhas, uma por atleta × prova × edição).
-- Resultado esperado nos dados reais: 51 linhas.
--
-- Regras e motivos
-- - games_id é o texto de Games, como veio. Nos dados reais, Games é sempre
--   exatamente Year || ' ' || Season, e cada Games tem um único Year e uma
--   única Season.
-- - Verão e Inverno do mesmo ano são edições distintas (spec).
-- - A cidade NÃO fica aqui (decisão H2): 1956 Summer teve duas cidades
--   (Melbourne e, só para o hipismo, Stockholm). Com city na dimensão, essa
--   edição viraria duas linhas e games_id deixaria de ser único. As cidades
--   ficam em refined.games_cities (03_games_cities.sql).
-- - year convertido para INTEGER com TRY_CAST, que devolve NULL em vez de
--   falhar; a contagem de falhas está no README (0 nos dados reais).
-- - TRIM em todos os textos e o texto 'NA' vira NULL (regra geral da refined).
--   Nos dados reais nenhuma dessas colunas tem 'NA' (perfil da unidade 3.1).
--
-- Aceite: games_id único e não nulo; year INTEGER; 51 linhas nos dados reais.
-- =============================================================================

CREATE OR REPLACE TABLE refined.games AS
WITH origem AS (
    SELECT DISTINCT
        NULLIF(NULLIF(TRIM("Games"), 'NA'), '') AS games_id,
        NULLIF(NULLIF(TRIM("Year"), 'NA'), '') AS year_texto,
        NULLIF(NULLIF(TRIM("Season"), 'NA'), '') AS season
    FROM raw.athlete_events
)
SELECT
    games_id,
    TRY_CAST(year_texto AS INTEGER) AS year,
    season
FROM origem
ORDER BY year, season;

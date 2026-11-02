-- =============================================================================
-- marts.evolucao_olimpica — ★ unidade 4.2 (mart 03)
-- =============================================================================
--
-- Pergunta: como os Jogos cresceram ao longo do tempo — quantos atletas,
-- países, modalidades e provas em cada edição?
--
-- Grão: edição (uma linha por games_id).
--
-- Origem: refined (athlete_results, events, games, games_cities). Não usa o
-- mart 01 porque ele não tem atletas nem provas.
--
-- Regras de contagem (spec, "Regras de contagem"):
-- - atletas: COUNT(DISTINCT athlete_id). Um atleta em várias provas da mesma
--   edição conta uma vez.
-- - paises: NOCs distintos (país = NOC; NOCs históricos ficam separados).
-- - modalidades: sports distintos; provas: event_id distintos.
-- - city: cidades-sede da edição, de refined.games_cities. Decisão H2: em
--   1956 Summer, com duas cidades, elas aparecem juntas em ordem alfabética
--   ('Melbourne | Stockholm'), para manter uma linha por edição sem perder
--   nenhuma cidade. Nas demais edições é só a cidade.
--
-- Exclusões (iguais às dos outros marts; H6 e H7):
-- - Art Competitions: fora das quatro contagens. Muda bastante 7 edições
--   (1912 a 1948); ex.: 1932 Summer tem 1.922 atletas com Art e 1.335 sem.
--   Nenhuma edição tinha só Art Competitions, então nenhuma some.
-- - Jogos de 1906: a edição não aparece.
--
-- Resultado nos dados reais: 50 linhas (51 edições menos 1906).
-- =============================================================================

CREATE OR REPLACE TABLE marts.evolucao_olimpica AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.games_id, r.athlete_id, r.noc, r.event_id, e.sport
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
contagens AS (
    SELECT
        games_id,
        COUNT(DISTINCT athlete_id) AS atletas,
        COUNT(DISTINCT noc) AS paises,
        COUNT(DISTINCT sport) AS modalidades,
        COUNT(DISTINCT event_id) AS provas
    FROM base
    GROUP BY games_id
),
cidades AS (
    SELECT games_id, STRING_AGG(city, ' | ' ORDER BY city) AS city
    FROM refined.games_cities
    GROUP BY games_id
)
SELECT
    g.games_id,
    g.year,
    g.season,
    c.city,
    ct.atletas,
    ct.paises,
    ct.modalidades,
    ct.provas
FROM contagens AS ct
JOIN refined.games AS g ON ct.games_id = g.games_id
LEFT JOIN cidades AS c ON ct.games_id = c.games_id
ORDER BY g.year, g.season;

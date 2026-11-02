-- =============================================================================
-- marts.medalhistas_extremos — unidade 4.3 (mart 14)
-- =============================================================================
--
-- Pergunta: quem foram os medalhistas mais jovens e mais velhos de cada
-- modalidade, no Verão e no Inverno?
--
-- Período: Verão de 1896 a 2016 e Inverno de 1924 a 2014 (só os CSVs de
-- origem; edições posteriores não estão no dataset).
--
-- Grão: modalidade × temporada × extremo ('mais jovem' / 'mais velho') ×
-- atleta. Todos os empatados ficam (decisão do usuário): escolher um entre
-- atletas com a mesma idade seria arbitrário e esconderia os outros. Nos
-- dados reais, até 5 atletas empatam no mesmo extremo de uma modalidade.
--
-- Origem: refined (athlete_results, events, games, athletes).
--
-- Regras:
-- - Só linhas com medalha e com idade preenchida. Medalhas sem idade ficam
--   de fora deste mart (573 nos dados reais); toda modalidade tem pelo menos
--   um medalhista com idade.
-- - Uma linha por atleta em cada extremo (decisão do usuário): medalhas diz
--   quantas ele ganhou com aquela idade, e provas lista as provas, juntas em
--   ordem alfabética.
-- - noc: os NOCs dessas medalhas, juntos em ordem alfabética.
-- - Se a modalidade tem uma idade só entre os medalhistas, o mesmo atleta
--   aparece como mais jovem e como mais velho.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): medalhas em Art
-- Competitions e nos Jogos de 1906 não contam.
-- =============================================================================

CREATE OR REPLACE TABLE marts.medalhistas_extremos AS
WITH medalhas AS (
    -- Medalhas com idade (exclusões acima).
    SELECT r.athlete_id, r.games_id, r.noc, r.age, e.sport, e.event, g.season
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
        AND r.medal IS NOT NULL
        AND r.age IS NOT NULL
),
limites AS (
    SELECT sport, season, MIN(age) AS idade_min, MAX(age) AS idade_max
    FROM medalhas
    GROUP BY sport, season
),
extremos AS (
    SELECT m.*, 'mais jovem' AS extremo
    FROM medalhas AS m
    JOIN limites AS l ON m.sport = l.sport AND m.season = l.season
    WHERE m.age = l.idade_min
    UNION ALL
    SELECT m.*, 'mais velho' AS extremo
    FROM medalhas AS m
    JOIN limites AS l ON m.sport = l.sport AND m.season = l.season
    WHERE m.age = l.idade_max
)
SELECT
    x.sport,
    x.season,
    x.extremo,
    x.age AS idade,
    x.athlete_id,
    a.name,
    a.sex,
    STRING_AGG(DISTINCT x.noc, ' | ' ORDER BY x.noc) AS noc,
    x.games_id,
    COUNT(*) AS medalhas,
    STRING_AGG(DISTINCT x.event, ' | ' ORDER BY x.event) AS provas
FROM extremos AS x
JOIN refined.athletes AS a ON x.athlete_id = a.athlete_id
GROUP BY x.sport, x.season, x.extremo, x.age, x.athlete_id, a.name, a.sex, x.games_id
ORDER BY x.season, x.sport, x.extremo, x.athlete_id;

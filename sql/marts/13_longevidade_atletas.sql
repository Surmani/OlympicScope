-- =============================================================================
-- marts.longevidade_atletas — unidade 4.3 (mart 13)
-- =============================================================================
--
-- Pergunta: quais atletas disputaram mais edições dos Jogos, e por quanto
-- tempo?
--
-- Grão: atleta. Só quem disputou 2 edições ou mais (decisão do usuário):
-- quem esteve numa edição só não tem longevidade para mostrar.
--
-- Origem: refined (athlete_results, events, games, athletes).
--
-- Regras:
-- - edicoes: edições disputadas, somando Verão e Inverno (é a carreira
--   olímpica inteira; 162 atletas competiram nas duas temporadas).
-- - primeiro_ano, ultimo_ano e anos_de_carreira (último − primeiro).
-- - noc: todos os NOCs que o atleta defendeu, juntos em ordem alfabética
--   (mesmo padrão do mart 08).
-- - ranking: mais edições primeiro; empate, mais anos de carreira. RANK():
--   empatados dividem a posição e a próxima pula.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): participações em Art
-- Competitions e nos Jogos de 1906 não contam como edição disputada.
-- =============================================================================

CREATE OR REPLACE TABLE marts.longevidade_atletas AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.athlete_id, r.games_id, r.noc, g.year
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
por_atleta AS (
    SELECT
        athlete_id,
        STRING_AGG(DISTINCT noc, ' | ' ORDER BY noc) AS noc,
        COUNT(DISTINCT games_id) AS edicoes,
        MIN(year) AS primeiro_ano,
        MAX(year) AS ultimo_ano,
        MAX(year) - MIN(year) AS anos_de_carreira
    FROM base
    GROUP BY athlete_id
    HAVING COUNT(DISTINCT games_id) >= 2
)
SELECT
    p.athlete_id,
    a.name,
    a.sex,
    p.noc,
    p.edicoes,
    p.primeiro_ano,
    p.ultimo_ano,
    p.anos_de_carreira,
    RANK() OVER (ORDER BY p.edicoes DESC, p.anos_de_carreira DESC) AS ranking
FROM por_atleta AS p
JOIN refined.athletes AS a ON p.athlete_id = a.athlete_id
ORDER BY ranking, p.athlete_id;

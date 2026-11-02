-- =============================================================================
-- marts.genero_por_pais — unidade 4.3 (mart 12)
-- =============================================================================
--
-- Pergunta: qual a participação de mulheres na delegação de cada país, em
-- cada edição?
--
-- Grão: NOC × edição, com todas as delegações (as mesmas 3.803 do mart 01).
-- Delegações sem nenhuma mulher (0%) ou sem nenhum homem (100%) ficam no mart:
-- é justamente o que ele quer mostrar.
--
-- Origem: refined (athlete_results, events, athletes, games, noc_regions).
--
-- Regras de contagem (mesmo padrão do mart 04):
-- - atletas_f, atletas_m e atletas: COUNT(DISTINCT athlete_id) da delegação;
--   quem disputou várias provas conta uma vez.
-- - percentual_mulheres: atletas_f ÷ atletas × 100, de 0 a 100, com 2 casas
--   (DECIMAL(5,2)).
-- - País = NOC, com region ao lado; NOCs históricos ficam separados.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions fora da
-- delegação; Jogos de 1906 fora do mart.
-- =============================================================================

CREATE OR REPLACE TABLE marts.genero_por_pais AS
WITH delegacao AS (
    SELECT
        r.games_id,
        r.noc,
        COUNT(DISTINCT r.athlete_id) FILTER (WHERE a.sex = 'F') AS atletas_f,
        COUNT(DISTINCT r.athlete_id) FILTER (WHERE a.sex = 'M') AS atletas_m,
        COUNT(DISTINCT r.athlete_id) AS atletas
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.athletes AS a ON r.athlete_id = a.athlete_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
    GROUP BY r.games_id, r.noc
)
SELECT
    d.noc,
    n.region,
    d.games_id,
    g.year,
    g.season,
    d.atletas_f,
    d.atletas_m,
    d.atletas,
    CAST(ROUND(100.0 * d.atletas_f / d.atletas, 2) AS DECIMAL(5, 2)) AS percentual_mulheres
FROM delegacao AS d
JOIN refined.games AS g ON d.games_id = g.games_id
LEFT JOIN refined.noc_regions AS n ON d.noc = n.noc
ORDER BY g.year, g.season, d.noc;

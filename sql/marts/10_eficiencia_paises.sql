-- =============================================================================
-- marts.eficiencia_paises — unidade 4.3 (mart 10)
-- =============================================================================
--
-- Pergunta: quantas medalhas cada país conquistou para cada 100 atletas que
-- enviou, em cada edição?
--
-- Grão: NOC × edição, com todos os países participantes (inclusive sem
-- medalha), igual ao mart 01.
--
-- Origem: marts.medalhas_por_pais_edicao (mart 01) para as medalhas, e
-- refined para o tamanho da delegação.
--
-- Regras de contagem:
-- - atletas: COUNT(DISTINCT athlete_id) do NOC na edição (o tamanho da
--   delegação); quem disputou várias provas conta uma vez.
-- - medalhas_conquistadas: do mart 01 (1 por time).
-- - medalhas_por_100_atletas: medalhas_conquistadas ÷ atletas × 100, com 2
--   casas. Por 100 atletas porque por atleta os números ficam pequenos e
--   difíceis de ler (ex.: 0,2250).
--
-- Cuidado na leitura: delegações muito pequenas distorcem a taxa. Um atleta
-- individual pode somar várias medalhas (ex.: 1896 AUS, 1 atleta e 3
-- medalhas = 300 por 100 atletas). A coluna atletas fica no mart para quem
-- exibe filtrar (ex.: WHERE atletas >= 10).
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions fora das
-- medalhas e da delegação; Jogos de 1906 fora do mart.
-- =============================================================================

CREATE OR REPLACE TABLE marts.eficiencia_paises AS
WITH delegacao AS (
    SELECT r.games_id, r.noc, COUNT(DISTINCT r.athlete_id) AS atletas
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
    GROUP BY r.games_id, r.noc
)
SELECT
    m.noc,
    m.region,
    m.games_id,
    m.year,
    m.season,
    d.atletas,
    m.medalhas_conquistadas,
    CAST(
        ROUND(100.0 * m.medalhas_conquistadas / d.atletas, 2) AS DECIMAL(7, 2)
    ) AS medalhas_por_100_atletas
FROM marts.medalhas_por_pais_edicao AS m
JOIN delegacao AS d ON m.games_id = d.games_id AND m.noc = d.noc
ORDER BY m.year, m.season, m.noc;

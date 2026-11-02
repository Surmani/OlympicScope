-- =============================================================================
-- marts.desempenho_esportivo — unidade 4.3 (mart 05)
-- =============================================================================
--
-- Pergunta: qual o tamanho de cada modalidade — quantas participações,
-- atletas, provas e medalhas — no Verão e no Inverno, somando toda a história?
--
-- Grão: modalidade × temporada.
--
-- Origem: refined (athlete_results, events, games).
--
-- Regras de contagem (spec, "Regras de contagem"):
-- - participacoes: linhas da fato (um atleta numa prova numa edição).
-- - atletas: COUNT(DISTINCT athlete_id). Quem disputou a modalidade em várias
--   edições conta uma vez.
-- - provas: event_id distintos que já existiram na modalidade.
-- - medalhas_conquistadas: combinação distinta de games_id + event_id + noc +
--   medal (um time campeão conta 1 ouro).
-- - registros_medalhistas: linhas com medalha (o mesmo time conta 1 por
--   jogador).
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions não
-- aparece; Jogos de 1906 fora das contagens.
-- =============================================================================

CREATE OR REPLACE TABLE marts.desempenho_esportivo AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.games_id, r.athlete_id, r.event_id, r.noc, r.medal, e.sport, g.season
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
)
SELECT
    sport,
    season,
    COUNT(*) AS participacoes,
    COUNT(DISTINCT athlete_id) AS atletas,
    COUNT(DISTINCT event_id) AS provas,
    COUNT(DISTINCT (games_id, event_id, noc, medal)) FILTER (
        WHERE medal IS NOT NULL
    ) AS medalhas_conquistadas,
    COUNT(*) FILTER (WHERE medal IS NOT NULL) AS registros_medalhistas
FROM base
GROUP BY sport, season
ORDER BY season, sport;

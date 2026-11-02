-- =============================================================================
-- marts.dominio_modalidade — unidade 4.3 (mart 11)
-- =============================================================================
--
-- Pergunta: quais países mais ganharam em cada modalidade, e com que fatia do
-- total de medalhas da modalidade?
--
-- Grão: modalidade × temporada × NOC. Só NOCs com pelo menos uma medalha na
-- modalidade (decisão do usuário): um ranking de domínio não precisa de quem
-- nunca ganhou naquele esporte (mesmo critério do mart 08).
--
-- Origem: refined (athlete_results, events, games, noc_regions).
--
-- Regras de contagem (spec, "Regras de contagem"):
-- - ouro, prata, bronze e medalhas_conquistadas: combinação distinta de
--   games_id + event_id + noc + medal. Uma prova em grupo conta 1 medalha
--   para o país (um time de basquete campeão = 1 ouro).
-- - percentual_medalhas: medalhas_conquistadas do NOC ÷ medalhas conquistadas
--   de todos os NOCs na modalidade × 100, com 2 casas. Motivo: as modalidades
--   têm tamanhos muito diferentes; domínio se mede melhor em proporção.
--   Por causa do arredondamento, a soma de uma modalidade pode não dar 100
--   exato: nos dados reais vai de 99,95 a 100,08.
-- - ranking_modalidade: critério do COI (ouro, prata, bronze) dentro de cada
--   modalidade × temporada, com RANK() (empatados dividem a posição).
-- - País = NOC, com region ao lado; NOCs históricos ficam separados.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions não
-- aparece; medalhas dos Jogos de 1906 não contam.
-- =============================================================================

CREATE OR REPLACE TABLE marts.dominio_modalidade AS
WITH medalhas AS (
    -- Uma linha por medalha conquistada (exclusões acima).
    SELECT DISTINCT e.sport, g.season, r.games_id, r.event_id, r.noc, r.medal
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
        AND r.medal IS NOT NULL
),
por_noc AS (
    SELECT
        sport,
        season,
        noc,
        COUNT(*) FILTER (WHERE medal = 'Gold') AS ouro,
        COUNT(*) FILTER (WHERE medal = 'Silver') AS prata,
        COUNT(*) FILTER (WHERE medal = 'Bronze') AS bronze,
        COUNT(*) AS medalhas_conquistadas
    FROM medalhas
    GROUP BY sport, season, noc
)
SELECT
    p.sport,
    p.season,
    p.noc,
    n.region,
    p.ouro,
    p.prata,
    p.bronze,
    p.medalhas_conquistadas,
    CAST(
        ROUND(
            100.0 * p.medalhas_conquistadas
            / SUM(p.medalhas_conquistadas) OVER (PARTITION BY p.sport, p.season),
            2
        ) AS DECIMAL(5, 2)
    ) AS percentual_medalhas,
    RANK() OVER (
        PARTITION BY p.sport, p.season
        ORDER BY p.ouro DESC, p.prata DESC, p.bronze DESC
    ) AS ranking_modalidade
FROM por_noc AS p
LEFT JOIN refined.noc_regions AS n ON p.noc = n.noc
ORDER BY p.season, p.sport, ranking_modalidade, p.noc;

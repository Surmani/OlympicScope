-- =============================================================================
-- marts.quadro_historico — ★ unidade 4.2 (mart 02)
-- =============================================================================
--
-- Pergunta: qual é o quadro de medalhas de todos os tempos de cada país
-- (NOC), separado entre Jogos de Verão e de Inverno?
--
-- Grão: NOC × temporada. Uma linha para cada NOC que participou de pelo
-- menos uma edição da temporada, inclusive os que nunca ganharam medalha.
--
-- Origem: marts.medalhas_por_pais_edicao (mart 01), que roda antes por causa
-- do prefixo do arquivo.
-- Motivo: as regras de contagem e as exclusões ficam escritas num lugar só
-- (o mart 01); se mudarem, os dois marts mudam juntos, e os totais dos dois
-- batem por construção. Somar por edição dá o mesmo total que contar direto
-- no histórico, porque toda medalha conquistada pertence a uma única edição
-- (a edição faz parte da combinação distinta da regra).
--
-- Regras de contagem (herdadas do mart 01, spec "Regras de contagem"):
-- - ouro, prata, bronze e medalhas_conquistadas: soma das medalhas
--   conquistadas (combinação distinta de games_id + event_id + noc + medal).
-- - registros_medalhistas: soma das linhas com medalha.
-- - edicoes_disputadas: edições da temporada em que o NOC participou
--   (= linhas do NOC no mart 01 naquela temporada).
-- - ranking_historico: critério do COI (ouro, depois prata, depois bronze),
--   dentro de cada temporada. RANK(): empatados dividem a posição e a
--   próxima pula (1, 2, 2, 4). NULL para quem nunca ganhou medalha.
-- - País = NOC, com region ao lado; NOCs históricos ficam separados.
--
-- Exclusões (aplicadas no mart 01): Art Competitions e Jogos de 1906.
--
-- Resultado nos dados reais: 347 linhas (228 NOCs no Verão, 119 no Inverno).
-- =============================================================================

CREATE OR REPLACE TABLE marts.quadro_historico AS
WITH totais AS (
    SELECT
        noc,
        region,
        season,
        SUM(ouro)::BIGINT AS ouro,
        SUM(prata)::BIGINT AS prata,
        SUM(bronze)::BIGINT AS bronze,
        SUM(medalhas_conquistadas)::BIGINT AS medalhas_conquistadas,
        SUM(registros_medalhistas)::BIGINT AS registros_medalhistas,
        COUNT(*) AS edicoes_disputadas
    FROM marts.medalhas_por_pais_edicao
    GROUP BY noc, region, season
)
SELECT
    *,
    -- Quem não tem medalha fica no fim da ordenação e não altera a posição
    -- dos medalhistas; depois recebe NULL.
    CASE
        WHEN medalhas_conquistadas > 0 THEN
            RANK() OVER (
                PARTITION BY season
                ORDER BY ouro DESC, prata DESC, bronze DESC
            )
    END AS ranking_historico
FROM totais
ORDER BY season, ranking_historico NULLS LAST, noc;

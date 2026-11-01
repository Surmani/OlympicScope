-- =============================================================================
-- marts.medalhas_por_pais_edicao — ★ unidade 4.2
-- =============================================================================
--
-- Pergunta: quantas medalhas cada país (NOC) conquistou em cada edição, e em
-- que posição ficou no quadro de medalhas daquela edição?
--
-- Grão: NOC × edição. Uma linha para cada NOC que participou da edição,
-- inclusive os que não ganharam medalha (com zeros).
--
-- Regras de contagem (spec, "Regras de contagem"):
-- - ouro, prata, bronze e medalhas_conquistadas: uma medalha por combinação
--   distinta de games_id + event_id + noc + medal. Um time de basquete
--   campeão conta 1 ouro, não 12.
-- - registros_medalhistas: linhas com medalha. O mesmo time conta 12.
-- - País = NOC, com region ao lado para consulta. NOCs históricos (URS, GDR,
--   FRG...) ficam separados.
-- - ranking_edicao: critério do COI — mais ouros; empate, mais pratas;
--   empate, mais bronzes. RANK(): NOCs empatados dividem a posição e a
--   próxima pula (1, 2, 2, 4), como nos quadros oficiais. NULL para quem
--   não ganhou medalha: não aparece no quadro.
--
-- Exclusões (confirmadas na investigação: H6 e H7):
-- - Art Competitions (sport = 'Art Competitions'): competição artística, não
--   esportiva; 3.578 linhas na raw.
-- - Jogos de 1906 (games_id = '1906 Summer'): não reconhecidos pelo COI;
--   1.733 linhas na raw. A edição não aparece no mart.
-- As linhas continuam na refined; só este mart as filtra.
--
-- Limitação conhecida da regra de contagem: em 19 casos a mesma
-- edição + prova + NOC + medalha aparece com mais de um Team. Alguns são duas
-- medalhas de verdade (ex.: KOR com dois bronzes no tênis de mesa em duplas
-- de 1992), que a regra conta como uma; outros são uma medalha só, com o
-- nome do cavalo em Team (hipismo por equipes de 2008). Como Team não separa
-- os dois casos com segurança, a regra da spec é mantida: no máximo 22
-- medalhas podem estar contadas a menos, de 18.534.
--
-- Resultado nos dados reais: 3.803 linhas (50 edições).
-- =============================================================================

CREATE OR REPLACE TABLE marts.medalhas_por_pais_edicao AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.games_id, r.event_id, r.noc, r.medal
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
participacao AS (
    -- Um registro por NOC × edição, com os registros de medalhistas.
    SELECT
        games_id,
        noc,
        COUNT(*) FILTER (WHERE medal IS NOT NULL) AS registros_medalhistas
    FROM base
    GROUP BY games_id, noc
),
medalhas AS (
    -- Uma linha por medalha conquistada (regra da spec).
    SELECT DISTINCT games_id, event_id, noc, medal
    FROM base
    WHERE medal IS NOT NULL
),
quadro AS (
    SELECT
        games_id,
        noc,
        COUNT(*) FILTER (WHERE medal = 'Gold') AS ouro,
        COUNT(*) FILTER (WHERE medal = 'Silver') AS prata,
        COUNT(*) FILTER (WHERE medal = 'Bronze') AS bronze
    FROM medalhas
    GROUP BY games_id, noc
),
juntos AS (
    SELECT
        p.noc,
        n.region,
        p.games_id,
        g.year,
        g.season,
        COALESCE(q.ouro, 0) AS ouro,
        COALESCE(q.prata, 0) AS prata,
        COALESCE(q.bronze, 0) AS bronze,
        COALESCE(q.ouro + q.prata + q.bronze, 0) AS medalhas_conquistadas,
        p.registros_medalhistas
    FROM participacao AS p
    JOIN refined.games AS g ON p.games_id = g.games_id
    LEFT JOIN refined.noc_regions AS n ON p.noc = n.noc
    LEFT JOIN quadro AS q ON p.games_id = q.games_id AND p.noc = q.noc
)
SELECT
    *,
    -- Quem não tem medalha fica no fim da ordenação e não altera a posição
    -- dos medalhistas; depois recebe NULL.
    CASE
        WHEN medalhas_conquistadas > 0 THEN
            RANK() OVER (
                PARTITION BY games_id
                ORDER BY ouro DESC, prata DESC, bronze DESC
            )
    END AS ranking_edicao
FROM juntos
ORDER BY year, season, ranking_edicao NULLS LAST, noc;

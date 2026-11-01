-- =============================================================================
-- refined.noc_regions — unidade 3.2a
-- =============================================================================
--
-- Grão: uma linha por código NOC.
-- Origem: raw.noc_regions (230 linhas).
-- Resultado esperado nos dados reais: 231 linhas (230 da origem + SGP).
--
-- Regras e motivos
-- - TRIM em todos os textos (regra geral da refined).
--   Nos dados reais nenhum valor tinha espaço sobrando: 0 linhas afetadas.
-- - O texto 'NA' vira NULL (regra geral da refined).
--   Afeta region em 3 linhas: ROT, TUV e UNK. Sem isso, os três apareceriam
--   agrupados como se 'NA' fosse o nome de uma região (ver H5 no README).
-- - O texto vazio '' também vira NULL.
--   Afeta notes em 209 linhas. Na refined toda ausência é NULL, para quem
--   consulta usar só IS NULL.
-- - Acrescenta a linha SGP com os dados da linha SIN, mantendo SIN.
--   Motivo (H4): os atletas de Singapura usam o NOC 'SGP' (349 linhas em
--   raw.athlete_events), que não existe em raw.noc_regions; lá Singapura
--   está como 'SIN', que nunca aparece nos atletas. Sem a linha SGP, essas
--   349 linhas ficariam sem região e a fato teria chave sem dimensão.
--   Nenhum registro da origem é apagado ou alterado. Se um dia a origem
--   trouxer SGP, a linha não é acrescentada (NOT EXISTS), e nada duplica.
-- - Nenhuma linha da origem é descartada.
--
-- Aceite: noc único e não nulo; 231 linhas nos dados reais;
-- region IS NULL exatamente para ROT, TUV e UNK.
-- =============================================================================

CREATE OR REPLACE TABLE refined.noc_regions AS
WITH origem AS (
    SELECT
        NULLIF(NULLIF(TRIM("NOC"), 'NA'), '') AS noc,
        NULLIF(NULLIF(TRIM("region"), 'NA'), '') AS region,
        NULLIF(NULLIF(TRIM("notes"), 'NA'), '') AS notes
    FROM raw.noc_regions
)
SELECT noc, region, notes
FROM origem
UNION ALL
SELECT 'SGP' AS noc, region, notes
FROM origem
WHERE noc = 'SIN'
    AND NOT EXISTS (SELECT 1 FROM origem WHERE noc = 'SGP')
ORDER BY noc;

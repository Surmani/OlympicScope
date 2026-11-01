-- =============================================================================
-- refined.games_cities — unidade 3.2b
-- =============================================================================
--
-- Grão: uma linha por par edição × cidade-sede.
-- Origem: raw.athlete_events (271.116 linhas).
-- Resultado esperado nos dados reais: 52 linhas (51 edições; 1956 Summer
-- tem duas cidades).
--
-- Regras e motivos
-- - Tabela criada pela decisão H2: 1956 Summer aparece com Melbourne
--   (4.829 linhas) e Stockholm (298 linhas, todas de Equestrianism).
--   Manter a cidade em refined.games quebraria o grão da dimensão; tirar a
--   cidade da refined faria o mart 03 (evolucao_olimpica) depender da raw.
--   Aqui nenhuma cidade se perde e cada tabela tem um grão limpo.
-- - TRIM e 'NA' → NULL (regra geral da refined).
--
-- Aceite: par (games_id, city) único; todo games_id existe em refined.games;
-- 52 linhas nos dados reais.
-- =============================================================================

CREATE OR REPLACE TABLE refined.games_cities AS
SELECT DISTINCT
    NULLIF(NULLIF(TRIM("Games"), 'NA'), '') AS games_id,
    NULLIF(NULLIF(TRIM("City"), 'NA'), '') AS city
FROM raw.athlete_events
ORDER BY games_id, city;

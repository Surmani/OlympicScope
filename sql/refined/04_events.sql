-- =============================================================================
-- refined.events — unidade 3.2c
-- =============================================================================
--
-- Grão: uma linha por prova (par sport + event).
-- Origem: raw.athlete_events (271.116 linhas).
-- Resultado esperado nos dados reais: 765 linhas.
--
-- Regras e motivos
-- - A combinação sport + event identifica uma prova (spec). Nos dados reais
--   são 765 provas distintas e 765 pares: nenhuma prova aparece em mais de
--   uma modalidade, e todas começam com o nome da modalidade.
-- - event_id gerado com ROW_NUMBER() ordenado por sport e depois event.
--   Motivo: determinístico; mesma entrada, mesmo id em toda execução, sem
--   depender da ordem em que as linhas foram lidas.
--   Aviso: o id é estável enquanto o conjunto de provas for o mesmo. Uma
--   prova nova na origem mudaria o id das que vêm depois dela na ordem
--   alfabética. O dataset é fixo (coletado em 2018), então isso não afeta
--   o projeto.
-- - Art Competitions fica na dimensão: a refined não descarta registros
--   válidos; a exclusão é feita nos marts.
-- - TRIM e 'NA' → NULL (regra geral da refined). Nos dados reais nenhum
--   valor de Sport ou Event tem espaço sobrando ou é 'NA'.
--
-- Aceite: event_id único, não nulo e sequencial de 1 a N; par (sport, event)
-- único; 765 linhas nos dados reais.
-- =============================================================================

CREATE OR REPLACE TABLE refined.events AS
WITH provas AS (
    SELECT DISTINCT
        NULLIF(NULLIF(TRIM("Sport"), 'NA'), '') AS sport,
        NULLIF(NULLIF(TRIM("Event"), 'NA'), '') AS event
    FROM raw.athlete_events
)
SELECT
    CAST(ROW_NUMBER() OVER (ORDER BY sport, event) AS INTEGER) AS event_id,
    sport,
    event
FROM provas
ORDER BY event_id;

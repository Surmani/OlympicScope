-- =============================================================================
-- marts.participacao_genero — ★ unidade 4.2 (mart 04)
-- =============================================================================
--
-- Pergunta: como mudou a participação de homens e mulheres ao longo das
-- edições?
--
-- Grão: edição × sexo. Toda edição tem as duas linhas (F e M), mesmo quando
-- um dos sexos não teve nenhum atleta.
-- Motivo: em 1896 Summer não houve mulheres. Com a linha F = 0, o gráfico
-- mostra 0% naquela edição em vez de um buraco; o dashboard só faz
-- SELECT ... WHERE e não pode completar linhas faltantes. O zero não é dado
-- inventado: é o resultado da contagem.
--
-- Origem: refined (athlete_results, events, athletes, games). sex vem de
-- refined.athletes (H3: cada atleta tem um único sexo).
--
-- Regras de contagem (spec, "Regras de contagem"):
-- - atletas: COUNT(DISTINCT athlete_id) do sexo na edição. Um atleta em
--   várias provas da mesma edição conta uma vez.
-- - percentual_atletas: atletas do sexo ÷ atletas da edição × 100, de 0 a
--   100, com 2 casas (DECIMAL(5,2)), mesmo padrão do peso. Por causa do
--   arredondamento, F + M de uma edição pode dar 99,99 ou 100,01.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions fora das
-- contagens; Jogos de 1906 fora do mart.
--
-- Resultado nos dados reais: 100 linhas (50 edições × 2 sexos).
-- =============================================================================

CREATE OR REPLACE TABLE marts.participacao_genero AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.games_id, r.athlete_id, a.sex
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.athletes AS a ON r.athlete_id = a.athlete_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
grade AS (
    -- Toda edição com todos os sexos que existem no dado (F e M).
    SELECT edicoes.games_id, sexos.sex
    FROM (SELECT DISTINCT games_id FROM base) AS edicoes
    CROSS JOIN (SELECT DISTINCT sex FROM base) AS sexos
),
contagens AS (
    SELECT games_id, sex, COUNT(DISTINCT athlete_id) AS atletas
    FROM base
    GROUP BY games_id, sex
),
juntos AS (
    SELECT
        gr.games_id,
        gr.sex,
        COALESCE(c.atletas, 0) AS atletas
    FROM grade AS gr
    LEFT JOIN contagens AS c ON gr.games_id = c.games_id AND gr.sex = c.sex
)
SELECT
    j.games_id,
    g.year,
    g.season,
    j.sex,
    j.atletas,
    CAST(
        ROUND(100.0 * j.atletas / SUM(j.atletas) OVER (PARTITION BY j.games_id), 2)
        AS DECIMAL(5, 2)
    ) AS percentual_atletas
FROM juntos AS j
JOIN refined.games AS g ON j.games_id = g.games_id
ORDER BY g.year, g.season, j.sex;

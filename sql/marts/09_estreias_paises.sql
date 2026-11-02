-- =============================================================================
-- marts.estreias_paises — unidade 4.3 (mart 09)
-- =============================================================================
--
-- Pergunta: quando cada país participou pela primeira vez, e quando ganhou a
-- primeira medalha e o primeiro ouro?
--
-- Grão: NOC × temporada (Verão e Inverno têm estreias diferentes).
--
-- Origem: marts.medalhas_por_pais_edicao (mart 01), que já tem uma linha por
-- NOC × edição com as medalhas conquistadas e as exclusões aplicadas.
-- Motivo: regras de contagem e exclusões escritas num lugar só.
--
-- Colunas:
-- - primeira_edicao / ano_primeira_edicao: primeira edição disputada.
-- - primeira_medalha / ano_primeira_medalha: primeira edição com pelo menos
--   uma medalha conquistada. NULL se o país nunca ganhou medalha.
-- - edicoes_ate_primeira_medalha: quantas edições o país disputou até a da
--   primeira medalha, contando ela (1 = ganhou já na estreia). NULL se nunca
--   ganhou.
-- - primeiro_ouro / ano_primeiro_ouro: primeira edição com ouro. NULL se
--   nunca ganhou ouro.
-- - Dentro de uma temporada cada ano tem uma única edição, por isso o ano
--   ordena as edições.
--
-- Exclusões (aplicadas no mart 01): Art Competitions e Jogos de 1906. Um país
-- cuja estreia foi em 1906 aparece com a estreia na edição seguinte.
-- =============================================================================

CREATE OR REPLACE TABLE marts.estreias_paises AS
WITH marcos AS (
    SELECT
        noc,
        region,
        season,
        ARG_MIN(games_id, year) AS primeira_edicao,
        MIN(year) AS ano_primeira_edicao,
        ARG_MIN(games_id, year) FILTER (WHERE medalhas_conquistadas > 0) AS primeira_medalha,
        MIN(year) FILTER (WHERE medalhas_conquistadas > 0) AS ano_primeira_medalha,
        ARG_MIN(games_id, year) FILTER (WHERE ouro > 0) AS primeiro_ouro,
        MIN(year) FILTER (WHERE ouro > 0) AS ano_primeiro_ouro
    FROM marts.medalhas_por_pais_edicao
    GROUP BY noc, region, season
),
ate_medalha AS (
    -- Edições disputadas até a da primeira medalha, contando ela.
    SELECT m.noc, m.season, COUNT(*) AS edicoes_ate_primeira_medalha
    FROM marcos AS m
    JOIN marts.medalhas_por_pais_edicao AS p
        ON m.noc = p.noc AND m.season = p.season AND p.year <= m.ano_primeira_medalha
    GROUP BY m.noc, m.season
)
SELECT
    m.noc,
    m.region,
    m.season,
    m.primeira_edicao,
    m.ano_primeira_edicao,
    m.primeira_medalha,
    m.ano_primeira_medalha,
    a.edicoes_ate_primeira_medalha,
    m.primeiro_ouro,
    m.ano_primeiro_ouro
FROM marcos AS m
LEFT JOIN ate_medalha AS a ON m.noc = a.noc AND m.season = a.season
ORDER BY m.season, m.ano_primeira_edicao, m.noc;

-- =============================================================================
-- Investigação das hipóteses H1–H8 — unidade 3.1
-- =============================================================================
--
-- Pergunta: o que o dado real diz sobre cada hipótese da spec (docs/SPEC.md,
-- seção "Hipóteses a verificar com contagens")?
--
-- Regras
-- - Só leitura: nenhuma tabela é criada ou alterada. Lê apenas o schema raw.
--   Motivo: a investigação informa as decisões da refined; ela não as toma.
-- - Todas as colunas da raw são VARCHAR e a ausência é o texto 'NA'
--   (unidade 2.2). Por isso as comparações são com texto e as conversões
--   usam TRY_CAST, que devolve NULL em vez de falhar.
-- - Os resultados estão registrados no README, seção "Hipóteses H1–H8".
--
-- Como rodar: abra o banco com `uv run python ui.py` e execute cada bloco.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Perfil de ausências: quantos valores são o texto 'NA' e quantos são texto
-- vazio '' em cada coluna.
-- Motivo: a spec diz que 'NA' aparece em Age, Height, Weight, Medal "e
-- possivelmente outras colunas"; e célula vazia chega à raw como ''.
-- A refined precisa saber exatamente quais colunas tratar.
-- -----------------------------------------------------------------------------
SELECT
    'athlete_events' AS tabela,
    coluna,
    COUNT(*) FILTER (WHERE valor = 'NA') AS texto_na,
    COUNT(*) FILTER (WHERE valor = '') AS texto_vazio
FROM (UNPIVOT raw.athlete_events ON COLUMNS(*) INTO NAME coluna VALUE valor)
GROUP BY coluna
UNION ALL
SELECT
    'noc_regions' AS tabela,
    coluna,
    COUNT(*) FILTER (WHERE valor = 'NA') AS texto_na,
    COUNT(*) FILTER (WHERE valor = '') AS texto_vazio
FROM (UNPIVOT raw.noc_regions ON COLUMNS(*) INTO NAME coluna VALUE valor)
GROUP BY coluna
ORDER BY tabela, coluna;


-- -----------------------------------------------------------------------------
-- H1: existem linhas duplicadas idênticas (as 15 colunas iguais)?
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*) AS grupos_duplicados,
    SUM(n)::BIGINT AS linhas_nos_grupos,
    SUM(n - 1)::BIGINT AS linhas_em_excesso
FROM (
    SELECT COUNT(*) AS n
    FROM raw.athlete_events
    GROUP BY
        "ID", "Name", "Sex", "Age", "Height", "Weight", "Team", "NOC",
        "Games", "Year", "Season", "City", "Sport", "Event", "Medal"
    HAVING COUNT(*) > 1
);

-- H1 (conferência por outro caminho): total de linhas menos linhas distintas.
SELECT
    t.linhas,
    d.linhas_distintas,
    t.linhas - d.linhas_distintas AS linhas_em_excesso
FROM
    (SELECT COUNT(*) AS linhas FROM raw.athlete_events) AS t,
    (SELECT COUNT(*) AS linhas_distintas FROM (SELECT DISTINCT * FROM raw.athlete_events)) AS d;

-- H1 (onde estão): linhas em excesso por modalidade, as 5 maiores.
SELECT "Sport", SUM(n - 1)::BIGINT AS linhas_em_excesso
FROM (
    SELECT "Sport", COUNT(*) AS n
    FROM raw.athlete_events
    GROUP BY
        "ID", "Name", "Sex", "Age", "Height", "Weight", "Team", "NOC",
        "Games", "Year", "Season", "City", "Sport", "Event", "Medal"
    HAVING COUNT(*) > 1
)
GROUP BY "Sport"
ORDER BY linhas_em_excesso DESC, "Sport"
LIMIT 5;


-- -----------------------------------------------------------------------------
-- H2: uma edição (Games) pode ter mais de uma cidade?
-- -----------------------------------------------------------------------------
SELECT
    "Games",
    COUNT(DISTINCT "City") AS cidades,
    STRING_AGG(DISTINCT "City", ' | ' ORDER BY "City") AS lista_cidades
FROM raw.athlete_events
GROUP BY "Games"
HAVING COUNT(DISTINCT "City") > 1
ORDER BY "Games";


-- -----------------------------------------------------------------------------
-- H3: um mesmo ID aparece com nomes ou sexo diferentes?
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE nomes > 1) AS ids_com_mais_de_um_nome,
    COUNT(*) FILTER (WHERE sexos > 1) AS ids_com_mais_de_um_sexo,
    COUNT(*) AS ids_distintos
FROM (
    SELECT "ID", COUNT(DISTINCT "Name") AS nomes, COUNT(DISTINCT "Sex") AS sexos
    FROM raw.athlete_events
    GROUP BY "ID"
);


-- -----------------------------------------------------------------------------
-- H4: existem NOCs em athlete_events que não estão em noc_regions?
-- -----------------------------------------------------------------------------
SELECT a."NOC", COUNT(*) AS linhas
FROM raw.athlete_events AS a
LEFT JOIN raw.noc_regions AS r ON a."NOC" = r."NOC"
WHERE r."NOC" IS NULL
GROUP BY a."NOC"
ORDER BY a."NOC";

-- H4 (sentido inverso): NOCs de noc_regions que nunca aparecem em athlete_events.
SELECT r."NOC", r."region"
FROM raw.noc_regions AS r
WHERE r."NOC" NOT IN (SELECT DISTINCT "NOC" FROM raw.athlete_events)
ORDER BY r."NOC";

-- H4 (detalhe): como o NOC sem correspondência aparece em athlete_events.
SELECT a."NOC", a."Team", MIN(a."Year") AS primeiro_ano, MAX(a."Year") AS ultimo_ano, COUNT(*) AS linhas
FROM raw.athlete_events AS a
LEFT JOIN raw.noc_regions AS r ON a."NOC" = r."NOC"
WHERE r."NOC" IS NULL
GROUP BY a."NOC", a."Team"
ORDER BY linhas DESC;


-- -----------------------------------------------------------------------------
-- H5: vários NOCs apontam para a mesma região?
-- -----------------------------------------------------------------------------
SELECT
    "region",
    COUNT(*) AS nocs,
    STRING_AGG("NOC", ', ' ORDER BY "NOC") AS lista_nocs
FROM raw.noc_regions
GROUP BY "region"
HAVING COUNT(*) > 1
ORDER BY nocs DESC, "region";

-- H5 (detalhe): NOCs cuja região é o texto 'NA' (apareceu agrupado acima).
SELECT "NOC", "region", "notes"
FROM raw.noc_regions
WHERE "region" = 'NA'
ORDER BY "NOC";


-- -----------------------------------------------------------------------------
-- H6: 'Art Competitions' aparece como modalidade?
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*) AS linhas,
    COUNT(DISTINCT "Games") AS edicoes,
    COUNT(DISTINCT "Event") AS provas,
    COUNT(DISTINCT "ID") AS atletas,
    MIN("Year") AS primeiro_ano,
    MAX("Year") AS ultimo_ano
FROM raw.athlete_events
WHERE "Sport" = 'Art Competitions';


-- -----------------------------------------------------------------------------
-- H7: os Jogos de 1906 (não reconhecidos pelo COI) estão no dataset?
-- -----------------------------------------------------------------------------
SELECT
    "Games",
    "Year",
    "Season",
    "City",
    COUNT(*) AS linhas,
    COUNT(DISTINCT "ID") AS atletas
FROM raw.athlete_events
WHERE "Year" = '1906'
GROUP BY ALL
ORDER BY "Games";


-- -----------------------------------------------------------------------------
-- H8: Height e Weight têm valores decimais?
-- preenchidos  = valores diferentes de 'NA'
-- com_ponto    = escritos com ponto decimal (ex.: '180.0')
-- fracionarios = com parte decimal diferente de zero (ex.: '72.5')
-- nao_numericos = preenchidos que não convertem para número
-- -----------------------------------------------------------------------------
SELECT
    coluna,
    COUNT(*) FILTER (WHERE valor <> 'NA') AS preenchidos,
    COUNT(*) FILTER (WHERE valor <> 'NA' AND valor LIKE '%.%') AS com_ponto,
    COUNT(*) FILTER (
        WHERE TRY_CAST(valor AS DOUBLE) <> FLOOR(TRY_CAST(valor AS DOUBLE))
    ) AS fracionarios,
    COUNT(*) FILTER (
        WHERE valor <> 'NA' AND TRY_CAST(valor AS DOUBLE) IS NULL
    ) AS nao_numericos
FROM (
    UNPIVOT (SELECT "Height", "Weight" FROM raw.athlete_events)
    ON "Height", "Weight" INTO NAME coluna VALUE valor
)
GROUP BY coluna
ORDER BY coluna;

-- H8 (exemplos): valores fracionários mais frequentes de cada coluna.
SELECT coluna, valor, COUNT(*) AS linhas
FROM (
    UNPIVOT (SELECT "Height", "Weight" FROM raw.athlete_events)
    ON "Height", "Weight" INTO NAME coluna VALUE valor
)
WHERE TRY_CAST(valor AS DOUBLE) <> FLOOR(TRY_CAST(valor AS DOUBLE))
GROUP BY coluna, valor
QUALIFY ROW_NUMBER() OVER (PARTITION BY coluna ORDER BY COUNT(*) DESC, valor) <= 5
ORDER BY coluna, linhas DESC, valor;

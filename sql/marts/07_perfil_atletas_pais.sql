-- =============================================================================
-- marts.perfil_atletas_pais — unidade 4.3 (mart 07)
-- =============================================================================
--
-- Pergunta: qual a idade, a altura e o peso médios dos atletas de cada país
-- (NOC), por sexo, no Verão e no Inverno?
--
-- Grão: NOC × sexo × temporada.
--
-- Origem: refined (athlete_results, events, athletes, games, noc_regions).
--
-- Regras (as mesmas do mart 06, trocando modalidade por país):
-- - Cada atleta entra UMA vez por edição pelo seu NOC, não uma vez por prova
--   (quem disputou várias provas na mesma edição não pesa mais na média).
-- - Um atleta que voltou em outra edição entra de novo, com os valores
--   daquela edição.
-- - Médias com 2 casas (DECIMAL(5,2)); altura em cm e peso em kg, exibidos
--   no padrão brasileiro pelo dashboard.
-- - Sem imputação; n_idade, n_altura e n_peso dizem sobre quantos atletas ×
--   edição cada média foi calculada.
-- - País = NOC, com region ao lado; NOCs históricos ficam separados.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions e Jogos
-- de 1906 fora das médias. Um NOC que só teve atletas nessas exclusões não
-- aparece.
-- =============================================================================

CREATE OR REPLACE TABLE marts.perfil_atletas_pais AS
WITH atleta_edicao AS (
    -- Um registro por atleta × edição × NOC (exclusões acima).
    SELECT DISTINCT
        r.athlete_id,
        r.games_id,
        r.noc,
        a.sex,
        g.season,
        r.age,
        r.height,
        r.weight
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    JOIN refined.athletes AS a ON r.athlete_id = a.athlete_id
    JOIN refined.games AS g ON r.games_id = g.games_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
)
SELECT
    ae.noc,
    n.region,
    ae.sex,
    ae.season,
    CAST(ROUND(AVG(ae.age), 2) AS DECIMAL(5, 2)) AS idade_media,
    CAST(ROUND(AVG(ae.height), 2) AS DECIMAL(5, 2)) AS altura_media,
    CAST(ROUND(AVG(ae.weight), 2) AS DECIMAL(5, 2)) AS peso_media,
    COUNT(ae.age) AS n_idade,
    COUNT(ae.height) AS n_altura,
    COUNT(ae.weight) AS n_peso
FROM atleta_edicao AS ae
LEFT JOIN refined.noc_regions AS n ON ae.noc = n.noc
GROUP BY ae.noc, n.region, ae.sex, ae.season
ORDER BY ae.season, ae.noc, ae.sex;

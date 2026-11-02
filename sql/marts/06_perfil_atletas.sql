-- =============================================================================
-- marts.perfil_atletas — unidade 4.3 (mart 06)
-- =============================================================================
--
-- Pergunta: qual a idade, a altura e o peso médios dos atletas de cada
-- modalidade, por sexo, no Verão e no Inverno?
--
-- Grão: modalidade × sexo × temporada.
--
-- Origem: refined (athlete_results, events, athletes, games).
--
-- Regras:
-- - Cada atleta entra UMA vez por edição em cada modalidade, não uma vez por
--   prova. Motivo: a média responde "qual a altura média dos atletas"; por
--   linha, quem disputou 15 provas na mesma edição pesaria 15 vezes. Nos
--   dados reais, nenhum atleta tem idade, altura ou peso diferentes entre as
--   provas da mesma edição (184.569 atletas × edição, 0 com valores
--   diferentes), então juntar as linhas não perde nada.
-- - Um atleta que voltou em outra edição entra de novo, com a idade, altura
--   e peso daquela edição (os valores mudam com o tempo).
-- - Médias com 2 casas (DECIMAL(5,2)). Unidades da refined: altura em
--   centímetros, peso em quilogramas; o dashboard exibe no padrão brasileiro
--   (ex.: 1,75 m e 63,50 kg).
-- - Ausências não são imputadas: a média usa só os valores preenchidos, e
--   n_idade, n_altura e n_peso dizem sobre quantos atletas × edição cada
--   média foi calculada. Grupos com poucos dados ficam no mart; quem exibe
--   decide filtrar (ex.: WHERE n_altura >= 10).
--
-- Exclusões (iguais às dos outros marts; H6 e H7): Art Competitions não
-- aparece; Jogos de 1906 fora das médias.
-- =============================================================================

CREATE OR REPLACE TABLE marts.perfil_atletas AS
WITH atleta_edicao AS (
    -- Um registro por atleta × edição × modalidade (exclusões acima).
    SELECT DISTINCT
        r.athlete_id,
        r.games_id,
        e.sport,
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
    sport,
    sex,
    season,
    CAST(ROUND(AVG(age), 2) AS DECIMAL(5, 2)) AS idade_media,
    CAST(ROUND(AVG(height), 2) AS DECIMAL(5, 2)) AS altura_media,
    CAST(ROUND(AVG(weight), 2) AS DECIMAL(5, 2)) AS peso_media,
    COUNT(age) AS n_idade,
    COUNT(height) AS n_altura,
    COUNT(weight) AS n_peso
FROM atleta_edicao
GROUP BY sport, sex, season
ORDER BY season, sport, sex;

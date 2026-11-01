-- =============================================================================
-- refined.athletes — unidade 3.2d
-- =============================================================================
--
-- Grão: uma linha por atleta.
-- Origem: raw.athlete_events (271.116 linhas; um atleta aparece uma vez por
-- prova em cada edição).
-- Resultado esperado nos dados reais: 135.571 linhas.
--
-- Regras e motivos
-- - athlete_id é o ID da origem convertido para INTEGER com TRY_CAST; a
--   contagem de falhas está no README (0 nos dados reais).
-- - Só ID, nome e sexo: idade, altura e peso mudam a cada participação e
--   ficam na fato (spec).
-- - H3 verificada antes: nenhum ID tem mais de um nome ou mais de um sexo,
--   então DISTINCT gera exatamente uma linha por atleta.
-- - Nomes iguais com IDs diferentes (713 nomes) são homônimos, pessoas
--   distintas: a chave é o ID, e eles continuam separados.
-- - Espaços excedentes em name: TRIM nas pontas e qualquer sequência de 2 ou
--   mais espaços no meio vira UM espaço (nunca zero).
--   Motivo: a spec manda remover espaços excedentes. name é a única coluna
--   do dataset com espaço sobrando (81 linhas da raw nas pontas, 237 com
--   espaço duplo no meio). 'João   Pedro' vira 'João Pedro', nunca
--   'JoãoPedro': o padrão ' {2,}' só casa com 2+ espaços e os troca por um.
-- - Os nomes vêm sem letras acentuadas (ex.: 'Mnica', 'Rukajrvi'): o CSV
--   original tem 0 bytes fora do ASCII, os acentos já foram removidos na
--   origem. Não há como recuperar; nada é feito aqui.
-- - 'NA' → NULL (regra geral da refined).
--
-- Aceite: athlete_id único, não nulo e INTEGER; nenhum nome com espaço nas
-- pontas ou duplo; as letras de cada nome iguais às da origem; 135.571 linhas.
-- =============================================================================

CREATE OR REPLACE TABLE refined.athletes AS
SELECT DISTINCT
    TRY_CAST(NULLIF(NULLIF(TRIM("ID"), 'NA'), '') AS INTEGER) AS athlete_id,
    NULLIF(NULLIF(REGEXP_REPLACE(TRIM("Name"), ' {2,}', ' ', 'g'), 'NA'), '') AS name,
    NULLIF(NULLIF(TRIM("Sex"), 'NA'), '') AS sex
FROM raw.athlete_events
ORDER BY athlete_id;

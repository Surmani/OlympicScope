-- =============================================================================
-- refined.athlete_results — tabela fato — unidade 3.3
-- =============================================================================
--
-- Grão: uma linha distinta da origem = uma participação registrada de um
-- atleta em uma prova de uma edição. Em edições antigas, o mesmo atleta pode
-- ter mais de uma linha na mesma prova com valores diferentes (89 casos nos
-- dados reais, ex.: várias regatas de Sailing 1900, Rowing 1900, vários
-- trabalhos em Art Competitions): essas linhas são mantidas.
-- Origem: raw.athlete_events (271.116 linhas).
-- Resultado esperado nos dados reais: 269.731 linhas.
--
-- Contagem por etapa (dados reais; conferida e registrada no README):
--   raw.athlete_events ....................... 271.116
--   depois de tirar linhas idênticas (H1) .... 269.731  (−1.385)
--   depois do JOIN com refined.events ........ 269.731  (o JOIN não muda nada)
--
-- Regras e motivos
-- - Linhas idênticas nas 15 colunas da origem saem, ficando uma (H1).
--   Motivo: uma cópia idêntica não acrescenta informação e infla contagens
--   de linhas (11 delas têm medalha e inflariam registros_medalhistas).
--   Saem 1.385 linhas (1.315 de Art Competitions).
--   Linhas que diferem em QUALQUER coluna ficam. Medalhas em provas
--   diferentes (ex.: 100 m e 200 m) têm Event diferente, então nunca são
--   tratadas como duplicata. As 89 repetições com medalha ou time diferente
--   na mesma prova também ficam.
-- - Tipos convertidos com TRY_CAST (devolve NULL em vez de falhar; falhas
--   contadas no README): athlete_id, age e height INTEGER (H8: altura sem
--   nenhum valor decimal); weight DECIMAL(5,2).
--   weight com 2 casas: decisão do usuário. 1.052 pesos têm 1 casa (ex.: 63.5)
--   e 6 têm 13 casas (74.6666666666667 e 77.3333333333333, 3 linhas cada),
--   que são arredondados para 74.67 e 77.33.
-- - Unidades como na origem, já no sistema métrico: height em centímetros,
--   weight em quilogramas (medianas: 175 cm e 70 kg).
-- - Idade, altura e peso NÃO são imputados: ausência continua NULL.
-- - 'NA' → NULL e TRIM em todos os textos (regra geral da refined).
--   medal fica só Gold, Silver, Bronze ou NULL.
-- - event_id vem de refined.events pelo par sport + event (mesma limpeza
--   aplicada aqui e lá, para o JOIN casar).
--
-- Aceite: 269.731 linhas; nenhuma linha idêntica; toda chave existe na
-- dimensão (athlete_id, games_id, event_id, noc); medal só nos 4 valores.
-- =============================================================================

CREATE OR REPLACE TABLE refined.athlete_results AS
WITH distintas AS (
    SELECT DISTINCT * FROM raw.athlete_events
),
limpas AS (
    SELECT
        TRY_CAST(NULLIF(NULLIF(TRIM("ID"), 'NA'), '') AS INTEGER) AS athlete_id,
        NULLIF(NULLIF(TRIM("Games"), 'NA'), '') AS games_id,
        NULLIF(NULLIF(TRIM("Sport"), 'NA'), '') AS sport,
        NULLIF(NULLIF(TRIM("Event"), 'NA'), '') AS event,
        NULLIF(NULLIF(TRIM("NOC"), 'NA'), '') AS noc,
        NULLIF(NULLIF(TRIM("Team"), 'NA'), '') AS team,
        TRY_CAST(NULLIF(NULLIF(TRIM("Age"), 'NA'), '') AS INTEGER) AS age,
        TRY_CAST(NULLIF(NULLIF(TRIM("Height"), 'NA'), '') AS INTEGER) AS height,
        TRY_CAST(NULLIF(NULLIF(TRIM("Weight"), 'NA'), '') AS DECIMAL(5, 2)) AS weight,
        NULLIF(NULLIF(TRIM("Medal"), 'NA'), '') AS medal
    FROM distintas
)
SELECT
    l.athlete_id,
    l.games_id,
    e.event_id,
    l.noc,
    l.team,
    l.age,
    l.height,
    l.weight,
    l.medal
FROM limpas AS l
LEFT JOIN refined.events AS e
    ON l.sport = e.sport AND l.event = e.event
ORDER BY l.games_id, e.event_id, l.athlete_id, l.noc, l.team, l.medal;

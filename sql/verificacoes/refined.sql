-- =============================================================================
-- Verificações da refined — unidade 3.4
-- =============================================================================
--
-- Executadas por pipeline/refined.py depois de criar as tabelas, a cada
-- execução, sobre os dados reais.
--
-- Pergunta: as garantias da refined continuam valendo?
-- Cada linha do resultado é uma verificação: nome e quantidade de problemas.
-- 0 problemas = ok. Qualquer valor acima de 0 faz a execução falhar.
--
-- Motivo: a spec manda GARANTIR que toda chave da fato exista na dimensão.
-- Os testes provam isso só com dados inventados; estas consultas provam com
-- os dados reais, e avisam se a raw ou um SQL da refined mudar.
--
-- Regra para chaves: um problema é uma linha com chave nula ou repetida.
-- Regra para órfãos: um problema é uma linha da fato (ou de games_cities)
-- cuja chave não existe na dimensão; chave nula também conta como órfã.
-- =============================================================================

SELECT verificacao, problemas
FROM (
    SELECT 1 AS ordem, 'noc_regions: noc único e não nulo' AS verificacao,
        COUNT(*) - COUNT(DISTINCT noc) + COUNT(*) FILTER (WHERE noc IS NULL) AS problemas
    FROM refined.noc_regions

    UNION ALL
    SELECT 2, 'games: games_id único e não nulo',
        COUNT(*) - COUNT(DISTINCT games_id) + COUNT(*) FILTER (WHERE games_id IS NULL)
    FROM refined.games

    UNION ALL
    SELECT 3, 'games_cities: par (games_id, city) único e não nulo',
        COUNT(*) - COUNT(DISTINCT (games_id, city))
        + COUNT(*) FILTER (WHERE games_id IS NULL OR city IS NULL)
    FROM refined.games_cities

    UNION ALL
    SELECT 4, 'games_cities: toda edição existe em games',
        COUNT(*) FILTER (WHERE g.games_id IS NULL)
    FROM refined.games_cities AS c
    LEFT JOIN refined.games AS g ON c.games_id = g.games_id

    UNION ALL
    SELECT 5, 'events: event_id e par (sport, event) únicos e não nulos',
        (COUNT(*) - COUNT(DISTINCT event_id))
        + (COUNT(*) - COUNT(DISTINCT (sport, event)))
        + COUNT(*) FILTER (WHERE event_id IS NULL OR sport IS NULL OR event IS NULL)
    FROM refined.events

    UNION ALL
    SELECT 6, 'athletes: athlete_id único e não nulo',
        COUNT(*) - COUNT(DISTINCT athlete_id) + COUNT(*) FILTER (WHERE athlete_id IS NULL)
    FROM refined.athletes

    UNION ALL
    SELECT 7, 'athlete_results: todo athlete_id existe em athletes',
        COUNT(*) FILTER (WHERE a.athlete_id IS NULL)
    FROM refined.athlete_results AS r
    LEFT JOIN refined.athletes AS a ON r.athlete_id = a.athlete_id

    UNION ALL
    SELECT 8, 'athlete_results: todo games_id existe em games',
        COUNT(*) FILTER (WHERE g.games_id IS NULL)
    FROM refined.athlete_results AS r
    LEFT JOIN refined.games AS g ON r.games_id = g.games_id

    UNION ALL
    SELECT 9, 'athlete_results: todo event_id existe em events',
        COUNT(*) FILTER (WHERE e.event_id IS NULL)
    FROM refined.athlete_results AS r
    LEFT JOIN refined.events AS e ON r.event_id = e.event_id

    UNION ALL
    SELECT 10, 'athlete_results: todo noc existe em noc_regions',
        COUNT(*) FILTER (WHERE n.noc IS NULL)
    FROM refined.athlete_results AS r
    LEFT JOIN refined.noc_regions AS n ON r.noc = n.noc

    UNION ALL
    SELECT 11, 'athlete_results: nenhuma linha idêntica',
        (SELECT COUNT(*) FROM refined.athlete_results)
        - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM refined.athlete_results))

    UNION ALL
    SELECT 12, 'athlete_results: medal só Gold, Silver, Bronze ou NULL',
        COUNT(*) FILTER (WHERE medal NOT IN ('Gold', 'Silver', 'Bronze'))
    FROM refined.athlete_results
)
ORDER BY ordem;

-- =============================================================================
-- marts.ranking_atletas — unidade 4.3 (mart 08)
-- =============================================================================
--
-- Pergunta: quem são os maiores medalhistas individuais da história?
--
-- Grão: atleta. Só atletas com pelo menos uma medalha (decisão do usuário):
-- um ranking de medalhas com mais de 100 mil atletas zerados não acrescenta
-- nada; quem disputou muitas edições sem medalha aparece no mart 13.
--
-- Origem: refined (athlete_results, events, athletes).
--
-- Regras de contagem:
-- - Aqui cada linha com medalha é UMA medalha do atleta (spec): no nível
--   individual, cada jogador de um time campeão ganhou, sim, um ouro. É
--   diferente de medalhas_conquistadas dos outros marts, que conta 1 por time.
-- - edicoes: edições em que o atleta competiu (com ou sem medalha).
-- - noc: todos os NOCs que o atleta defendeu em qualquer participação,
--   juntos em ordem alfabética (ex.: 'GDR | GER'). Motivo: 767 medalhistas
--   competiram por mais de um país (319 deles ganharam medalha por mais de
--   um; ex.: Birgit Fischer, GDR e GER); mostrar só um esconderia parte da
--   carreira. Mesmo padrão das cidades de 1956 no mart 03.
-- - ranking: critério do COI (ouro, depois prata, depois bronze), com RANK():
--   empatados dividem a posição e a próxima pula.
--
-- Exclusões (iguais às dos outros marts; H6 e H7): medalhas e participações
-- em Art Competitions e nos Jogos de 1906 não contam.
-- =============================================================================

CREATE OR REPLACE TABLE marts.ranking_atletas AS
WITH base AS (
    -- Participações que entram nos indicadores (exclusões acima).
    SELECT r.athlete_id, r.games_id, r.noc, r.medal
    FROM refined.athlete_results AS r
    JOIN refined.events AS e ON r.event_id = e.event_id
    WHERE e.sport <> 'Art Competitions'
        AND r.games_id <> '1906 Summer'
),
por_atleta AS (
    SELECT
        athlete_id,
        STRING_AGG(DISTINCT noc, ' | ' ORDER BY noc) AS noc,
        COUNT(*) FILTER (WHERE medal = 'Gold') AS ouro,
        COUNT(*) FILTER (WHERE medal = 'Silver') AS prata,
        COUNT(*) FILTER (WHERE medal = 'Bronze') AS bronze,
        COUNT(medal) AS total_medalhas,
        COUNT(DISTINCT games_id) AS edicoes
    FROM base
    GROUP BY athlete_id
    HAVING COUNT(medal) > 0
)
SELECT
    p.athlete_id,
    a.name,
    a.sex,
    p.noc,
    p.ouro,
    p.prata,
    p.bronze,
    p.total_medalhas,
    p.edicoes,
    RANK() OVER (ORDER BY p.ouro DESC, p.prata DESC, p.bronze DESC) AS ranking
FROM por_atleta AS p
JOIN refined.athletes AS a ON p.athlete_id = a.athlete_id
ORDER BY ranking, p.athlete_id;

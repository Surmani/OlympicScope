"""Consultas do dashboard — unidades 5.1 (Medalhas, Países) e 5.2 (Atletas, Os Jogos).

Cada função devolve uma ``Consulta`` (texto SQL + parâmetros); quem executa é
``executar``. Assim os testes rodam exatamente o mesmo SQL sobre marts
inventados em memória, e conferem o texto de cada consulta.

Regras e motivos
----------------

- Só o schema ``marts`` e só ``SELECT ... WHERE`` (com ``ORDER BY`` para a
  ordem de exibição). Nada de ``SUM``, ``AVG``, ``COUNT``, ``GROUP BY`` ou
  ``JOIN``.
  Motivo: regra do dashboard na spec. Cada mart já vem no grão exato em que
  é exibido; regra de negócio no app ficaria escondida, sem SQL versionado.
- Valores de filtro sempre como parâmetro (``?``), nunca colados no texto.
  Motivo: o texto da consulta fica fixo e auditável, e não há como um valor
  escolhido na tela virar SQL.
- O banco é aberto em modo leitura, só pelo tempo da consulta, e fechado em
  seguida (o cache fica no app, com ``st.cache_data``).
  Motivo: ninguém altera nada pela tela, e o pipeline pode rodar com o
  dashboard aberto (sem lock permanente).
- Este módulo não importa o ``pipeline`` e calcula o caminho do banco a
  partir do próprio arquivo.
  Motivo: com ``streamlit run app/app.py`` a raiz do projeto não está no
  caminho do Python; e o app não pode criar banco (``pipeline.db.conectar``
  criaria).

Critérios de aceite (verificados em ``tests/test_app_consultas.py``)
------------------------------------------------------------------

1. Toda consulta roda sobre os marts criados a partir da refined inventada.
2. Nenhuma consulta tem ``SUM``, ``AVG``, ``COUNT``, ``GROUP BY`` ou ``JOIN``,
   nem lê ``refined`` ou ``raw``; todas leem ``marts``.
3. Os filtros devolvem só as linhas pedidas.
"""

from pathlib import Path
from typing import NamedTuple

import duckdb
import pandas as pd

CAMINHO_BANCO = Path(__file__).resolve().parent.parent / "data" / "olympics.duckdb"


class Consulta(NamedTuple):
    sql: str
    parametros: tuple = ()


def banco_existe(caminho: Path = CAMINHO_BANCO) -> bool:
    return caminho.is_file()


def executar(consulta: Consulta, caminho: Path = CAMINHO_BANCO) -> pd.DataFrame:
    """Abre o banco em modo leitura, roda a consulta e fecha."""
    con = duckdb.connect(str(caminho), read_only=True)
    try:
        return con.execute(consulta.sql, list(consulta.parametros)).df()
    finally:
        con.close()


# --- listas para os filtros -------------------------------------------------------


def edicoes(season: str) -> Consulta:
    return Consulta(
        "SELECT games_id, year, city FROM marts.evolucao_olimpica "
        "WHERE season = ? ORDER BY year DESC",
        (season,),
    )


def paises(season: str) -> Consulta:
    return Consulta(
        "SELECT noc, region FROM marts.quadro_historico WHERE season = ? ORDER BY noc",
        (season,),
    )


def paises_com_medalha(season: str) -> Consulta:
    """Só os NOCs que já ganharam pelo menos uma medalha na temporada."""
    return Consulta(
        "SELECT noc, region FROM marts.quadro_historico "
        "WHERE season = ? AND medalhas_conquistadas > 0 ORDER BY noc",
        (season,),
    )


def modalidades(season: str) -> Consulta:
    return Consulta(
        "SELECT sport FROM marts.desempenho_esportivo WHERE season = ? ORDER BY sport",
        (season,),
    )


# --- página Medalhas --------------------------------------------------------------


def quadro_edicao(games_id: str) -> Consulta:
    return Consulta(
        "SELECT ranking_edicao, noc, region, ouro, prata, bronze, "
        "medalhas_conquistadas, registros_medalhistas "
        "FROM marts.medalhas_por_pais_edicao "
        "WHERE games_id = ? AND medalhas_conquistadas > 0 "
        "ORDER BY ranking_edicao, noc",
        (games_id,),
    )


def pais_por_edicao(noc: str, season: str) -> Consulta:
    return Consulta(
        "SELECT games_id, year, ouro, prata, bronze, medalhas_conquistadas, "
        "registros_medalhistas, ranking_edicao "
        "FROM marts.medalhas_por_pais_edicao "
        "WHERE noc = ? AND season = ? ORDER BY year",
        (noc, season),
    )


def quadro_historico(season: str) -> Consulta:
    return Consulta(
        "SELECT ranking_historico, noc, region, ouro, prata, bronze, "
        "medalhas_conquistadas, registros_medalhistas, edicoes_disputadas "
        "FROM marts.quadro_historico "
        "WHERE season = ? AND medalhas_conquistadas > 0 "
        "ORDER BY ranking_historico, noc",
        (season,),
    )


def ranking_atletas(limite: int) -> Consulta:
    return Consulta(
        "SELECT ranking, name, sex, noc, ouro, prata, bronze, total_medalhas, edicoes "
        "FROM marts.ranking_atletas WHERE ranking <= ? ORDER BY ranking, name",
        (limite,),
    )


def dominio_modalidade(sport: str, season: str) -> Consulta:
    return Consulta(
        "SELECT ranking_modalidade, noc, region, ouro, prata, bronze, "
        "medalhas_conquistadas, percentual_medalhas "
        "FROM marts.dominio_modalidade "
        "WHERE sport = ? AND season = ? ORDER BY ranking_modalidade, noc",
        (sport, season),
    )


# --- página Países ----------------------------------------------------------------


def estreias(season: str, so_com_medalha: bool = False) -> Consulta:
    # so_com_medalha = TRUE esconde quem nunca ganhou medalha na temporada.
    return Consulta(
        "SELECT noc, region, primeira_edicao, ano_primeira_edicao, primeira_medalha, "
        "ano_primeira_medalha, edicoes_ate_primeira_medalha, primeiro_ouro, "
        "ano_primeiro_ouro FROM marts.estreias_paises "
        "WHERE season = ? AND (NOT ? OR primeira_medalha IS NOT NULL) "
        "ORDER BY ano_primeira_edicao, noc",
        (season, so_com_medalha),
    )


def eficiencia(
    games_id: str, delegacao_minima: int, so_com_medalha: bool = False
) -> Consulta:
    # so_com_medalha = TRUE esconde quem não ganhou medalha na edição.
    return Consulta(
        "SELECT noc, region, atletas, medalhas_conquistadas, medalhas_por_100_atletas "
        "FROM marts.eficiencia_paises "
        "WHERE games_id = ? AND atletas >= ? AND (NOT ? OR medalhas_conquistadas > 0) "
        "ORDER BY medalhas_por_100_atletas DESC, noc",
        (games_id, delegacao_minima, so_com_medalha),
    )


def genero_pais(noc: str, season: str) -> Consulta:
    return Consulta(
        "SELECT games_id, year, atletas_f, atletas_m, atletas, percentual_mulheres "
        "FROM marts.genero_por_pais WHERE noc = ? AND season = ? ORDER BY year",
        (noc, season),
    )


def perfil_paises(season: str, sex: str, minimo_atletas: int) -> Consulta:
    return Consulta(
        "SELECT noc, region, idade_media, altura_media, peso_media, "
        "n_idade, n_altura, n_peso FROM marts.perfil_atletas_pais "
        "WHERE season = ? AND sex = ? AND n_altura >= ? ORDER BY altura_media DESC, noc",
        (season, sex, minimo_atletas),
    )


# --- página Atletas ---------------------------------------------------------------


def perfil_modalidades(season: str, sex: str, minimo_atletas: int) -> Consulta:
    return Consulta(
        "SELECT sport, idade_media, altura_media, peso_media, n_idade, n_altura, n_peso "
        "FROM marts.perfil_atletas "
        "WHERE season = ? AND sex = ? AND n_altura >= ? ORDER BY altura_media DESC, sport",
        (season, sex, minimo_atletas),
    )


def longevidade(limite: int) -> Consulta:
    return Consulta(
        "SELECT ranking, name, sex, noc, edicoes, primeiro_ano, ultimo_ano, "
        "anos_de_carreira FROM marts.longevidade_atletas "
        "WHERE ranking <= ? ORDER BY ranking, name",
        (limite,),
    )


def extremos(sport: str, season: str) -> Consulta:
    return Consulta(
        "SELECT extremo, idade, name, sex, noc, games_id, medalhas, provas "
        "FROM marts.medalhistas_extremos "
        "WHERE sport = ? AND season = ? ORDER BY extremo, name",
        (sport, season),
    )


# --- página Os Jogos --------------------------------------------------------------


def evolucao(season: str) -> Consulta:
    return Consulta(
        "SELECT games_id, year, city, atletas, paises, modalidades, provas "
        "FROM marts.evolucao_olimpica WHERE season = ? ORDER BY year",
        (season,),
    )


def participacao_genero(season: str) -> Consulta:
    return Consulta(
        "SELECT games_id, year, sex, atletas, percentual_atletas "
        "FROM marts.participacao_genero WHERE season = ? ORDER BY year, sex",
        (season,),
    )


def desempenho_modalidades(season: str) -> Consulta:
    return Consulta(
        "SELECT sport, participacoes, atletas, provas, medalhas_conquistadas, "
        "registros_medalhistas FROM marts.desempenho_esportivo "
        "WHERE season = ? ORDER BY participacoes DESC, sport",
        (season,),
    )


def programa(season: str) -> Consulta:
    return Consulta(
        "SELECT sport, primeira_edicao, primeiro_ano, ultima_edicao, ultimo_ano, "
        "edicoes, ausencias, no_programa_atual FROM marts.programa_olimpico "
        "WHERE season = ? ORDER BY primeiro_ano, sport",
        (season,),
    )

"""Testes de app/consultas.py.

Nenhum teste abre data/olympics.duckdb: os marts são criados num banco em
tmp_path, rodando os SQL reais de sql/marts/ sobre a refined inventada dos
testes dos marts. As consultas rodam pelo mesmo executar() do app.
"""

import re

import duckdb
import pytest
from test_marts_sql import criar_refined_inventada

from app import consultas
from pipeline import executor_sql, marts

# Uma chamada de exemplo para cada consulta do app.
CONSULTAS = {
    "edicoes": consultas.edicoes("Summer"),
    "paises": consultas.paises("Summer"),
    "paises_com_medalha": consultas.paises_com_medalha("Winter"),
    "modalidades": consultas.modalidades("Summer"),
    "quadro_edicao": consultas.quadro_edicao("2016 Summer"),
    "pais_por_edicao": consultas.pais_por_edicao("BRA", "Summer"),
    "quadro_historico": consultas.quadro_historico("Summer"),
    "ranking_atletas": consultas.ranking_atletas(10),
    "dominio_modalidade": consultas.dominio_modalidade("Athletics", "Summer"),
    "estreias": consultas.estreias("Summer", True),
    "eficiencia": consultas.eficiencia("2016 Summer", 1, True),
    "genero_pais": consultas.genero_pais("BRA", "Summer"),
    "perfil_paises": consultas.perfil_paises("Summer", "M", 1),
    "perfil_modalidades": consultas.perfil_modalidades("Summer", "M", 1),
    "longevidade": consultas.longevidade(10),
    "extremos": consultas.extremos("Swimming", "Summer"),
    "evolucao": consultas.evolucao("Summer"),
    "participacao_genero": consultas.participacao_genero("Summer"),
    "desempenho_modalidades": consultas.desempenho_modalidades("Summer"),
    "programa": consultas.programa("Winter"),
}


@pytest.fixture(scope="module")
def banco(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("app") / "teste.duckdb"
    conexao = duckdb.connect(str(caminho))
    criar_refined_inventada(conexao)
    executor_sql.executar(conexao, marts.PASTA_SQL, "marts")
    conexao.close()
    return caminho


def rodar(consulta, banco):
    return consultas.executar(consulta, banco)


# --- regra do dashboard: só SELECT ... WHERE em marts -----------------------------


@pytest.mark.parametrize("nome", CONSULTAS)
def test_consulta_so_le_marts_sem_agregacao(nome):
    sql = CONSULTAS[nome].sql.upper()

    assert sql.startswith("SELECT ")
    assert "FROM MARTS." in sql
    proibidos = r"\b(SUM|AVG|COUNT|MIN|MAX|GROUP BY|JOIN|REFINED\.|RAW\.)\b|\bOVER\s*\("
    assert re.search(proibidos, sql) is None, sql


@pytest.mark.parametrize("nome", CONSULTAS)
def test_valores_de_filtro_vao_como_parametro(nome):
    consulta = CONSULTAS[nome]
    assert consulta.sql.count("?") == len(consulta.parametros)
    for valor in consulta.parametros:
        assert f"'{valor}'" not in consulta.sql


@pytest.mark.parametrize("nome", CONSULTAS)
def test_toda_consulta_roda_nos_marts(nome, banco):
    assert len(rodar(CONSULTAS[nome], banco).columns) > 0


def test_banco_existe(tmp_path, banco):
    assert consultas.banco_existe(banco)
    assert not consultas.banco_existe(tmp_path / "nao_existe.duckdb")


def test_executar_abre_em_modo_leitura(banco):
    consulta = consultas.Consulta("CREATE TABLE marts.invasora AS SELECT 1 AS x")
    with pytest.raises(duckdb.Error):
        consultas.executar(consulta, banco)


# --- filtros devolvem só o que foi pedido -------------------------------------------


def test_edicoes_da_temporada_da_mais_recente_para_a_mais_antiga(banco):
    assert rodar(consultas.edicoes("Summer"), banco)["games_id"].tolist() == [
        "2016 Summer",
        "2012 Summer",
    ]
    assert rodar(consultas.edicoes("Winter"), banco)["games_id"].tolist() == [
        "2014 Winter"
    ]


def test_quadro_edicao_so_medalhistas_na_ordem_do_ranking(banco):
    df = rodar(consultas.quadro_edicao("2016 Summer"), banco)
    assert df["noc"].tolist() == ["BRA", "JAM", "KEN", "USA", "CAN"]  # ARG sem medalha


def test_pais_por_edicao_filtra_pais_e_temporada(banco):
    df = rodar(consultas.pais_por_edicao("BRA", "Summer"), banco)
    assert df["games_id"].tolist() == ["2012 Summer", "2016 Summer"]


def test_ranking_atletas_respeita_o_limite(banco):
    df = rodar(consultas.ranking_atletas(6), banco)
    assert df["ranking"].max() == 1
    assert len(df) == 6


def test_eficiencia_respeita_a_delegacao_minima(banco):
    df = rodar(consultas.eficiencia("2016 Summer", 3), banco)
    assert df["noc"].tolist() == ["BRA", "USA"]  # 4 e 3 atletas; os outros têm 1


def test_perfil_paises_respeita_o_minimo_de_atletas(banco):
    df = rodar(consultas.perfil_paises("Summer", "M", 3), banco)
    assert df["noc"].tolist() == ["BRA", "USA"]  # ARG tem só 1 altura


def test_perfil_modalidades_respeita_sexo_e_minimo(banco):
    df = rodar(consultas.perfil_modalidades("Summer", "M", 4), banco)
    assert df["sport"].tolist() == ["Basketball"]  # atletismo M tem 3 alturas


def test_extremos_da_modalidade(banco):
    df = rodar(consultas.extremos("Swimming", "Summer"), banco)
    assert df[["extremo", "name"]].values.tolist() == [
        ["mais jovem", "A11"],
        ["mais velho", "A13"],
    ]


def test_evolucao_e_genero_filtram_a_temporada(banco):
    assert rodar(consultas.evolucao("Winter"), banco)["games_id"].tolist() == [
        "2014 Winter"
    ]
    assert rodar(consultas.participacao_genero("Winter"), banco)["sex"].tolist() == [
        "F",
        "M",
    ]


def test_programa_e_desempenho_filtram_a_temporada(banco):
    assert rodar(consultas.programa("Winter"), banco)["sport"].tolist() == [
        "Alpine Skiing"
    ]
    assert rodar(consultas.desempenho_modalidades("Summer"), banco)[
        "sport"
    ].tolist() == ["Athletics", "Basketball", "Swimming"]


# --- filtro "só países com medalha" -------------------------------------------------


def test_paises_com_medalha_tira_quem_nunca_ganhou(banco):
    # No Inverno, BRA participou (2014) mas nunca ganhou medalha.
    assert rodar(consultas.paises("Winter"), banco)["noc"].tolist() == [
        "BRA",
        "CAN",
        "USA",
    ]
    assert rodar(consultas.paises_com_medalha("Winter"), banco)["noc"].tolist() == [
        "CAN",
        "USA",
    ]


def test_estreias_so_com_medalha(banco):
    todos = rodar(consultas.estreias("Summer", False), banco)["noc"].tolist()
    com_medalha = rodar(consultas.estreias("Summer", True), banco)["noc"].tolist()
    assert "ARG" in todos
    assert "ARG" not in com_medalha
    assert len(com_medalha) == len(todos) - 1


def test_eficiencia_so_com_medalha_na_edicao(banco):
    todos = rodar(consultas.eficiencia("2016 Summer", 1, False), banco)
    com_medalha = rodar(consultas.eficiencia("2016 Summer", 1, True), banco)
    assert "ARG" in todos["noc"].tolist()
    assert com_medalha["medalhas_conquistadas"].min() > 0
    assert len(com_medalha) == len(todos) - 1

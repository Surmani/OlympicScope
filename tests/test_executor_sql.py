"""Testes de pipeline/executor_sql.py.

SQL inventados em tmp_path e DuckDB em memória; nada lê raw/ nem o banco real.
Os três primeiros testes vieram de tests/test_refined.py (unidade 3.2a) e
passaram a usar o executor genérico com o schema como parâmetro.
"""

import duckdb
import pytest

from pipeline import executor_sql


@pytest.fixture
def con():
    conexao = duckdb.connect()
    yield conexao
    conexao.close()


def test_nome_tabela_tira_prefixo():
    assert executor_sql.nome_tabela("01_noc_regions.sql") == "noc_regions"
    assert executor_sql.nome_tabela("12_athlete_results.sql") == "athlete_results"
    assert (
        executor_sql.nome_tabela("01_medalhas_por_pais_edicao.sql")
        == "medalhas_por_pais_edicao"
    )


def test_executa_em_ordem_de_nome(tmp_path, con):
    (tmp_path / "02_segunda.sql").write_text(
        "CREATE OR REPLACE TABLE refined.segunda AS SELECT COUNT(*) AS n FROM "
        "refined.primeira",
        encoding="utf-8",
    )
    (tmp_path / "01_primeira.sql").write_text(
        "CREATE OR REPLACE TABLE refined.primeira AS SELECT 1 AS x",
        encoding="utf-8",
    )
    contagens = executor_sql.executar(con, tmp_path, "refined")

    assert list(contagens) == ["refined.primeira", "refined.segunda"]


def test_sql_que_nao_cria_a_tabela_do_nome_gera_erro(tmp_path, con):
    (tmp_path / "01_esperada.sql").write_text(
        "CREATE OR REPLACE TABLE refined.outra AS SELECT 1 AS x", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="refined.esperada"):
        executor_sql.executar(con, tmp_path, "refined")


def test_tabela_criada_em_outro_schema_gera_erro(tmp_path, con):
    # O SQL cria marts.x, mas foi executado pedindo o schema refined.
    con.execute("CREATE SCHEMA marts")
    (tmp_path / "01_x.sql").write_text(
        "CREATE OR REPLACE TABLE marts.x AS SELECT 1 AS a", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="refined.x"):
        executor_sql.executar(con, tmp_path, "refined")


def test_cria_o_schema_e_devolve_contagens_do_banco(tmp_path, con):
    (tmp_path / "01_tres.sql").write_text(
        "CREATE OR REPLACE TABLE marts.tres AS SELECT * FROM range(3)",
        encoding="utf-8",
    )
    assert executor_sql.executar(con, tmp_path, "marts") == {"marts.tres": 3}

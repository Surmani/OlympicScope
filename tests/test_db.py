"""Testes de pipeline/db.py.

Nenhum teste abre data/olympics.duckdb nem lê raw/: usam DuckDB em memória
ou em tmp_path, com dados inventados.
"""

import importlib

import duckdb
import pandas as pd
import pytest

from pipeline import db


@pytest.fixture
def con():
    conexao = duckdb.connect()
    yield conexao
    conexao.close()


def test_caminhos_sao_absolutos_e_independem_do_diretorio_corrente(
    tmp_path, monkeypatch
):
    antes = (db.PASTA_RAW, db.CAMINHO_BANCO)
    monkeypatch.chdir(tmp_path)
    recarregado = importlib.reload(db)

    assert recarregado.PASTA_RAW.is_absolute()
    assert recarregado.CAMINHO_BANCO.is_absolute()
    assert (recarregado.PASTA_RAW, recarregado.CAMINHO_BANCO) == antes
    assert recarregado.PASTA_RAW.name == "raw"
    assert recarregado.CAMINHO_BANCO.parent.name == "data"
    assert recarregado.CAMINHO_BANCO.name == "olympics.duckdb"


def test_conectar_cria_pasta_e_arquivo(tmp_path, monkeypatch):
    caminho = tmp_path / "data" / "teste.duckdb"
    monkeypatch.setattr(db, "CAMINHO_BANCO", caminho)

    conexao = db.conectar()
    try:
        assert conexao.execute("SELECT 1").fetchone()[0] == 1
    finally:
        conexao.close()

    assert caminho.parent.is_dir()
    assert caminho.is_file()


def test_criar_schema_e_idempotente(con):
    db.criar_schema(con, "raw")
    db.criar_schema(con, "raw")

    schemas = con.execute(
        "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'raw'"
    ).fetchone()[0]
    assert schemas == 1


def test_gravar_preserva_colunas_tipos_e_texto_na(con):
    df = pd.DataFrame(
        {
            "Medal": pd.Series(["Gold", "NA"], dtype=str),
            "Age": pd.Series(["24", "NA"], dtype=str),
            "Inteiro": pd.Series([1, 2], dtype="int64"),
        }
    )
    db.criar_schema(con, "raw")
    db.gravar(con, df, "raw", "exemplo")

    colunas = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND table_name = 'exemplo' ORDER BY "
        "ordinal_position"
    ).fetchall()
    assert colunas == [("Medal", "VARCHAR"), ("Age", "VARCHAR"), ("Inteiro", "BIGINT")]

    linhas = con.execute(
        'SELECT "Medal", "Age" FROM raw.exemplo ORDER BY "Inteiro"'
    ).fetchall()
    assert linhas == [("Gold", "24"), ("NA", "NA")]


def test_gravar_devolve_contagem_do_banco(con):
    df = pd.DataFrame({"a": ["x", "y", "z"]})
    db.criar_schema(con, "raw")

    assert db.gravar(con, df, "raw", "t") == 3


def test_gravar_duas_vezes_substitui_sem_duplicar(con):
    db.criar_schema(con, "raw")
    db.gravar(con, pd.DataFrame({"a": ["x", "y", "z"]}), "raw", "t")
    contagem = db.gravar(con, pd.DataFrame({"a": ["w"]}), "raw", "t")

    assert contagem == 1
    assert con.execute("SELECT a FROM raw.t").fetchall() == [("w",)]


def test_gravar_nao_deixa_view_nem_tabela_temporaria(con):
    db.criar_schema(con, "raw")
    db.gravar(con, pd.DataFrame({"a": ["x"]}), "raw", "t")

    views = con.execute(
        "SELECT COUNT(*) FROM duckdb_views() WHERE NOT internal"
    ).fetchone()[0]
    temporarias = con.execute(
        "SELECT COUNT(*) FROM duckdb_tables() WHERE temporary"
    ).fetchone()[0]
    assert views == 0
    assert temporarias == 0


def test_gravar_nao_deixa_view_quando_falha(con):
    # Schema inexistente faz o CREATE falhar; a view temporária ainda deve sumir.
    with pytest.raises(duckdb.CatalogException):
        db.gravar(con, pd.DataFrame({"a": ["x"]}), "nao_existe", "t")

    views = con.execute(
        "SELECT COUNT(*) FROM duckdb_views() WHERE NOT internal"
    ).fetchone()[0]
    assert views == 0

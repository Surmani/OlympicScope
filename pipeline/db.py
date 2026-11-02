"""Módulo de conexão com o DuckDB — unidade 1.1.

Primeiro código do projeto. Todas as etapas (ingestão, refined, marts)
importam este arquivo, por isso ele faz o mínimo e nada além disso.

Expõe exatamente:

- ``PASTA_RAW``: ``Path`` da pasta ``raw/``.
- ``CAMINHO_BANCO``: ``Path`` de ``data/olympics.duckdb``.
- ``conectar()``: abre o banco, criando a pasta ``data/`` e o arquivo se faltarem.
- ``criar_schema(con, nome)``: ``CREATE SCHEMA IF NOT EXISTS``.
- ``gravar(con, df, schema, tabela)``: ``CREATE OR REPLACE TABLE`` com as
  colunas e os tipos do DataFrame, sem alterar nada; devolve a contagem
  lida do banco.

Regras e motivos
----------------

- Caminhos resolvidos a partir do próprio ``db.py``, nunca do diretório corrente.
  Motivo: rodar um script de outra pasta não pode criar um banco vazio no
  lugar errado, que pareceria ingestão quebrada.
- Só isso, nada mais: este módulo não lê CSV, não conhece nome de tabela,
  não imprime nada e não converte tipo.
  Motivo: todas as etapas importam este arquivo; uma regra de negócio
  escondida aqui valeria para todas sem aparecer em nenhuma spec.
- ``gravar`` não converte tipo: a tabela recebe os tipos que o DataFrame já
  tem (um DataFrame só de texto vira uma tabela só de VARCHAR).
  Motivo: conversão de tipo é decisão, e decisões ficam na etapa que as toma.
- ``gravar`` não deixa view nem tabela temporária para trás, mesmo se der erro.
  Motivo: um objeto esquecido aparece no explorador do banco e confunde a
  leitura do que foi de fato gravado.
- ``gravar`` devolve a contagem lida do banco, não ``len(df)``.
  Motivo: o número que importa é o do que foi gravado, não o do que estava
  na memória.
- ``gravar`` é idempotente (``CREATE OR REPLACE TABLE``) e não cria o schema;
  ele precisa existir antes, via ``criar_schema``.
  Motivo: rodar o pipeline duas vezes tem que dar o mesmo resultado, e cada
  função faz uma coisa só.
- ``conectar()`` devolve a conexão aberta; quem chama é quem fecha.
  Nenhuma conexão global.
  Motivo: o arquivo ``.duckdb`` aceita um único processo escrevendo; uma
  conexão esquecida aberta trava o ``ui.py`` ou a próxima execução.

Critérios de aceite (verificados em ``tests/test_db.py``)
---------------------------------------------------------

1. ``PASTA_RAW`` e ``CAMINHO_BANCO`` são absolutos e não mudam quando o
   diretório corrente muda.
2. ``conectar()`` cria a pasta ``data/`` e o arquivo do banco quando não existem.
3. ``criar_schema`` chamado duas vezes não dá erro.
4. ``gravar`` preserva colunas e tipos: texto ``"NA"`` continua sendo o texto
   ``"NA"`` em uma coluna VARCHAR; um inteiro continua inteiro.
5. ``gravar`` devolve a contagem de linhas lida do banco.
6. ``gravar`` duas vezes na mesma tabela substitui o conteúdo, sem duplicar.
7. Depois de ``gravar``, o banco não tem nenhuma view nem tabela temporária.
"""

from pathlib import Path

import duckdb
import pandas as pd

_RAIZ = Path(__file__).resolve().parent.parent

PASTA_RAW = _RAIZ / "raw"
CAMINHO_BANCO = _RAIZ / "data" / "olympics.duckdb"

_VIEW_TEMPORARIA = "_gravar_df"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre o banco do projeto, criando a pasta e o arquivo se faltarem."""
    # CAMINHO_BANCO é lido na hora da chamada (não fixado na definição),
    # o que permite aos testes apontá-lo para um arquivo temporário.
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(CAMINHO_BANCO))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria o schema se ele ainda não existir."""
    con.execute(f'CREATE SCHEMA IF NOT EXISTS "{nome}"')


def gravar(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    schema: str,
    tabela: str,
) -> int:
    """Grava o df em schema.tabela sem alterar nada; devolve a contagem do banco."""
    destino = f'"{schema}"."{tabela}"'
    con.register(_VIEW_TEMPORARIA, df)
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {destino} AS SELECT * FROM {_VIEW_TEMPORARIA}"
        )
    finally:
        con.unregister(_VIEW_TEMPORARIA)
    # fetchall, não fetchone: no DuckDB 2.x um resultado lido pela metade
    # deixa a conexão ocupada e quebra o próximo uso por quem chamou.
    return con.execute(f"SELECT COUNT(*) FROM {destino}").fetchall()[0][0]

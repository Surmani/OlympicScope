"""Executor de pastas de SQL — usado pela refined e pelos marts. Unidade 4.1.

Executa, em ordem de nome, os arquivos ``NN_<tabela>.sql`` de uma pasta. Cada
arquivo cria uma tabela com ``CREATE OR REPLACE TABLE <schema>.<tabela>``.

Extraído de ``pipeline/refined.py`` (unidade 3.2a) quando os marts passaram a
precisar exatamente do mesmo comportamento, só com outro schema.

Regras e motivos
----------------

- Nenhuma regra de negócio aqui: as transformações ficam nos arquivos SQL.
  Motivo: cada decisão sobre o dado precisa estar escrita, com o motivo, no
  SQL que a aplica.
- Ordem pelo prefixo numérico do nome do arquivo (``01_``, ``02_``...).
  Motivo: uma tabela pode depender de outra criada antes; a ordem fica
  visível na própria pasta.
- O nome da tabela vem do nome do arquivo sem o prefixo, e o executor confere
  que a tabela foi criada no schema certo.
  Motivo: um SQL que cria a tabela com outro nome passaria em silêncio e a
  contagem devolvida seria de outra coisa.
- Devolve a contagem de cada tabela lida do banco; quem chama decide como
  imprimir.
- Um único lugar para esse comportamento.
  Motivo: com duas cópias, uma correção feita numa seria esquecida na outra.

Critérios de aceite (verificados em ``tests/test_executor_sql.py``)
------------------------------------------------------------------

1. Os SQL são executados em ordem de nome.
2. ``nome_tabela("01_noc_regions.sql")`` devolve ``"noc_regions"``.
3. Um SQL que não cria a tabela com o nome do arquivo, no schema pedido,
   gera erro claro.
4. O schema é criado se não existir.
"""

from pathlib import Path

import duckdb

from pipeline import db


def arquivos_sql(pasta: Path) -> list[Path]:
    """Devolve os arquivos .sql da pasta em ordem de nome."""
    return sorted(pasta.glob("*.sql"))


def nome_tabela(arquivo: Path | str) -> str:
    """Tira o prefixo numérico do nome do arquivo: 01_noc_regions.sql → noc_regions."""
    return Path(arquivo).stem.split("_", 1)[1]


def executar(
    con: duckdb.DuckDBPyConnection, pasta: Path, schema: str
) -> dict[str, int]:
    """Executa os SQL da pasta em ordem e devolve a contagem de cada tabela criada."""
    db.criar_schema(con, schema)
    contagens = {}
    for arquivo in arquivos_sql(pasta):
        tabela = nome_tabela(arquivo)
        con.execute(arquivo.read_text(encoding="utf-8"))
        existe = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = ? AND table_name = ?",
            [schema, tabela],
        ).fetchall()[0][0]
        if not existe:
            raise RuntimeError(f"{arquivo.name} não criou a tabela {schema}.{tabela}")
        contagens[f"{schema}.{tabela}"] = con.execute(
            f'SELECT COUNT(*) FROM "{schema}"."{tabela}"'
        ).fetchall()[0][0]
    return contagens

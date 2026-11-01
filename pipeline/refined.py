"""Refined: schema raw → schema refined, executando os SQL de sql/refined/.

Como rodar: ``uv run python -m pipeline.refined`` (depois da ingestão).

Unidade 3.2a — executor da refined
==================================

Executa, em ordem de nome, os arquivos ``sql/refined/NN_<tabela>.sql``. Cada
arquivo cria uma tabela com ``CREATE OR REPLACE TABLE refined.<tabela>``.

Regras e motivos
----------------

- As transformações ficam nos arquivos SQL, não aqui.
  Motivo: cada decisão sobre o dado precisa estar escrita, com o motivo, no
  SQL que a aplica; este executor não tem regra de negócio.
- Ordem pelo prefixo numérico do nome do arquivo (``01_``, ``02_``...).
  Motivo: dimensões precisam existir antes da fato; a ordem fica visível na
  própria pasta.
- O nome da tabela vem do nome do arquivo sem o prefixo
  (``01_noc_regions.sql`` → ``refined.noc_regions``), e o executor confere
  que a tabela foi criada.
  Motivo: um SQL que cria a tabela com outro nome passaria em silêncio e a
  contagem impressa seria de outra coisa.
- Ao final, uma linha por tabela com a contagem lida do banco e milhar
  separado por ponto, como na ingestão. A contagem de origem de cada
  tabela está no comentário do topo do SQL e no README.
  Motivo: diferença de contagem sem explicação é erro, e só dá para ver se
  o número aparece.
- Idempotente: rodar duas vezes dá o mesmo resultado (``CREATE OR REPLACE``).
- A pasta dos SQL é resolvida a partir deste arquivo, nunca do diretório corrente.
- ``stdout`` reconfigurado para UTF-8 dentro do ``main()``; conexão fechada
  num ``finally``.

Critérios de aceite (verificados em ``tests/test_refined.py``)
-------------------------------------------------------------

1. Os SQL são executados em ordem de nome.
2. ``nome_tabela("01_noc_regions.sql")`` devolve ``"noc_regions"``.
3. Um SQL que não cria a tabela com o nome do arquivo gera erro claro.
4. Rodar duas vezes imprime exatamente a mesma coisa.
5. ``refined.noc_regions``: texto aparado, 'NA' e '' viram NULL, linha SGP
   acrescentada a partir de SIN sem duplicar, nenhuma linha descartada.
"""

import sys
from pathlib import Path

import duckdb

from pipeline import db
from pipeline.ingestao import formatar_milhar

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql" / "refined"


def arquivos_sql(pasta: Path) -> list[Path]:
    """Devolve os arquivos .sql da pasta em ordem de nome."""
    return sorted(pasta.glob("*.sql"))


def nome_tabela(arquivo: Path | str) -> str:
    """Tira o prefixo numérico do nome do arquivo: 01_noc_regions.sql → noc_regions."""
    return Path(arquivo).stem.split("_", 1)[1]


def executar(con: duckdb.DuckDBPyConnection, pasta: Path) -> dict[str, int]:
    """Executa os SQL da pasta em ordem e devolve a contagem de cada tabela criada."""
    db.criar_schema(con, "refined")
    contagens = {}
    for arquivo in arquivos_sql(pasta):
        tabela = nome_tabela(arquivo)
        con.execute(arquivo.read_text(encoding="utf-8"))
        existe = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'refined' AND table_name = ?",
            [tabela],
        ).fetchall()[0][0]
        if not existe:
            raise RuntimeError(f"{arquivo.name} não criou a tabela refined.{tabela}")
        contagens[f"refined.{tabela}"] = con.execute(
            f'SELECT COUNT(*) FROM refined."{tabela}"'
        ).fetchall()[0][0]
    return contagens


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = db.conectar()
    try:
        contagens = executar(con, PASTA_SQL)
    finally:
        con.close()
    for tabela, linhas in contagens.items():
        print(f"{tabela}: {formatar_milhar(linhas)} linhas")


if __name__ == "__main__":
    main()

"""Refined: schema raw → schema refined, executando os SQL de sql/refined/.

Como rodar: ``uv run python -m pipeline.refined`` (depois da ingestão).

Unidade 3.2a — executor da refined
==================================

Executa, em ordem de nome, os arquivos ``sql/refined/NN_<tabela>.sql``. Cada
arquivo cria uma tabela com ``CREATE OR REPLACE TABLE refined.<tabela>``.

Desde a unidade 4.1, a execução genérica da pasta (ordem, nome da tabela,
conferência e contagem) fica em ``pipeline/executor_sql.py``, compartilhada
com os marts; as regras abaixo continuam valendo, agora aplicadas por lá.

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

1. Os SQL são executados em ordem de nome. (desde a 4.1: ``tests/test_executor_sql.py``)
2. ``nome_tabela("01_noc_regions.sql")`` devolve ``"noc_regions"``. (idem)
3. Um SQL que não cria a tabela com o nome do arquivo gera erro claro. (idem)
4. Rodar duas vezes imprime exatamente a mesma coisa.
5. ``refined.noc_regions``: texto aparado, 'NA' e '' viram NULL, linha SGP
   acrescentada a partir de SIN sem duplicar, nenhuma linha descartada.

Unidade 3.4 — verificações a cada execução
==========================================

Depois de criar as tabelas, executa ``sql/verificacoes/refined.sql``: cada
linha do resultado é uma verificação (chaves únicas e não nulas, nenhum
órfão da fato nas dimensões, nenhuma linha idêntica, medalhas válidas) com
a quantidade de problemas.

Regras e motivos
----------------

- As verificações rodam sobre os dados reais em toda execução.
  Motivo: a spec manda garantir que toda chave da fato exista na dimensão;
  os testes só provam isso com dados inventados. Se a raw ou um SQL da
  refined mudar, a execução avisa em vez de gerar marts errados em silêncio.
- As regras das verificações ficam no SQL, não aqui (mesmo motivo do executor).
- Tudo ok: imprime ``verificações: N de N ok`` depois das contagens.
  Alguma falha: lista em ``stderr`` cada verificação com problema e a
  quantidade, e encerra com ``sys.exit(1)``. As tabelas ficam no banco para
  investigar no ``ui.py``.
  Motivo: falhar alto é melhor do que seguir para os marts com chave órfã.

Critérios de aceite (verificados em ``tests/test_refined.py``)
-------------------------------------------------------------

6. Com dados consistentes, todas as verificações dão 0 problemas.
7. Um NOC na fato que não existe em ``noc_regions`` é apontado pela
   verificação de órfãos, e ``main()`` encerra com código 1 listando-a em
   ``stderr``.
8. Uma chave repetida numa dimensão é apontada pela verificação de unicidade.
"""

import sys
from pathlib import Path

import duckdb

from pipeline import db, executor_sql
from pipeline.ingestao import formatar_milhar

_RAIZ = Path(__file__).resolve().parent.parent
PASTA_SQL = _RAIZ / "sql" / "refined"
ARQUIVO_VERIFICACOES = _RAIZ / "sql" / "verificacoes" / "refined.sql"


def executar(con: duckdb.DuckDBPyConnection, pasta: Path) -> dict[str, int]:
    """Executa os SQL da pasta no schema refined (via executor_sql)."""
    return executor_sql.executar(con, pasta, "refined")


def verificar(con: duckdb.DuckDBPyConnection, arquivo: Path) -> list[tuple[str, int]]:
    """Executa o SQL de verificações e devolve (verificação, problemas) de cada uma."""
    return con.execute(arquivo.read_text(encoding="utf-8")).fetchall()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = db.conectar()
    try:
        contagens = executar(con, PASTA_SQL)
        resultados = verificar(con, ARQUIVO_VERIFICACOES)
    finally:
        con.close()

    for tabela, linhas in contagens.items():
        print(f"{tabela}: {formatar_milhar(linhas)} linhas")

    falhas = [(nome, problemas) for nome, problemas in resultados if problemas > 0]
    if falhas:
        print(
            f"verificações: {len(falhas)} de {len(resultados)} falharam",
            file=sys.stderr,
        )
        for nome, problemas in falhas:
            print(
                f"  - {nome}: {formatar_milhar(problemas)} problemas", file=sys.stderr
            )
        sys.exit(1)
    print(f"verificações: {len(resultados)} de {len(resultados)} ok")


if __name__ == "__main__":
    main()

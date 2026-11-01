"""Marts: schema refined → schema marts, executando os SQL de sql/marts/.

Como rodar: ``uv run python -m pipeline.marts`` (depois da refined).

Unidade 4.1 — executor dos marts
================================

Executa, em ordem de nome, os arquivos ``sql/marts/NN_<mart>.sql``. Cada
arquivo cria uma tabela com ``CREATE OR REPLACE TABLE marts.<mart>``
(ex.: ``01_medalhas_por_pais_edicao.sql`` → ``marts.medalhas_por_pais_edicao``).
Os marts em si entram um por unidade, a partir da 4.2.

Regras e motivos
----------------

- A execução da pasta é a mesma da refined e fica em
  ``pipeline/executor_sql.py`` (ordem pelo prefixo, nome da tabela tirado do
  arquivo e conferido, contagem lida do banco).
  Motivo: um único lugar para esse comportamento; uma correção vale para as
  duas camadas.
- As regras de cada indicador ficam no SQL do mart, com comentário no topo
  (pergunta, grão, regras de contagem, exclusões), não aqui.
- Se ``sql/marts/`` não tiver nenhum SQL, avisa em ``stderr`` onde procurou e
  encerra com ``sys.exit(1)``, antes de abrir o banco.
  Motivo: um pipeline que não gera nada e termina com sucesso parece que
  funcionou.
- Ao final, uma linha por mart com a contagem lida do banco, milhar separado
  por ponto, como nas outras etapas.
- Idempotente (``CREATE OR REPLACE``); pasta resolvida a partir deste arquivo;
  ``stdout`` reconfigurado para UTF-8 dentro do ``main()``; conexão fechada
  num ``finally``.

Critérios de aceite (verificados em ``tests/test_marts.py``)
-----------------------------------------------------------

1. Com SQL na pasta, cria cada ``marts.<mart>`` e imprime as contagens.
2. Rodar duas vezes imprime exatamente a mesma coisa.
3. Com a pasta vazia, encerra com código 1, mensagem em ``stderr`` com a
   pasta procurada, e não cria o arquivo do banco.
"""

import sys
from pathlib import Path

from pipeline import db, executor_sql
from pipeline.ingestao import formatar_milhar

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql" / "marts"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    # PASTA_SQL é lido na hora da chamada, o que permite aos testes
    # apontá-lo para uma pasta temporária.
    if not executor_sql.arquivos_sql(PASTA_SQL):
        print(f"Nenhum SQL de mart encontrado em {PASTA_SQL}.", file=sys.stderr)
        sys.exit(1)

    con = db.conectar()
    try:
        contagens = executor_sql.executar(con, PASTA_SQL, "marts")
    finally:
        con.close()
    for tabela, linhas in contagens.items():
        print(f"{tabela}: {formatar_milhar(linhas)} linhas")


if __name__ == "__main__":
    main()

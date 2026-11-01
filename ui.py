"""Explorador do banco no navegador — unidade 2.4.

Como rodar: ``uv run python ui.py`` e abrir http://localhost:4213
(o navegador abre sozinho). Ctrl+C encerra.

Abre ``data/olympics.duckdb`` com a extensão ``ui`` do DuckDB
(``INSTALL ui; LOAD ui; CALL start_ui()``). Na primeira execução o
``INSTALL ui`` baixa a extensão da internet; depois ela fica em cache.

Regras e motivos
----------------

- Fica de pé até Ctrl+C; no Ctrl+C fecha a conexão e sai sem traceback.
  Motivo: o arquivo ``.duckdb`` não aceita outro processo escrevendo enquanto
  está aberto; com o ``ui.py`` de pé, o pipeline falha com erro de lock.
  Sair limpo deixa claro que o banco foi liberado.
- Não cria banco: se ``data/olympics.duckdb`` não existir, avisa que é preciso
  rodar a ingestão e sai com ``sys.exit(1)``. Por isso não usa
  ``pipeline.db.conectar()``, que criaria o arquivo.
  Motivo: um banco vazio aberto no navegador parece ingestão quebrada.
- Abre o banco somente para leitura (``read_only=True``).
  Motivo: uma tabela criada à mão no navegador ficaria no banco sem ter
  saído do pipeline nem de um SQL versionado, e quebraria a rastreabilidade.
- ``ui.py`` e o pipeline não se importam. Por isso o caminho do banco é
  calculado aqui, a partir do próprio ``ui.py``, e não lido de
  ``pipeline.db.CAMINHO_BANCO`` — a duplicação é intencional.
  Motivo: o explorador é uma ferramenta à parte; o pipeline não pode
  depender dele, e ele não pode puxar regras do pipeline.
- Caminho resolvido a partir do próprio arquivo, nunca do diretório corrente.
  Motivo: rodar de outra pasta não pode procurar o banco no lugar errado.
- ``stdout`` reconfigurado para UTF-8.
  Motivo: no Windows os acentos saem embaralhados no terminal por padrão.

Critérios de aceite
-------------------

1. Sem o arquivo do banco, sai com código 1, a mensagem vai para ``stderr``
   com o caminho procurado e o comando da ingestão, e nenhum arquivo ou
   pasta é criado. (``tests/test_ui.py``)
2. ``ui.py`` não importa ``pipeline``, e nenhum módulo de ``pipeline`` importa
   ``ui``. (``tests/test_ui.py``)
3. Com o banco existente, http://localhost:4213 responde e mostra as tabelas
   do schema ``raw``. (verificação manual)
4. Ctrl+C fecha a conexão, imprime uma mensagem de encerramento e sai sem
   traceback. (verificação manual)
"""

import sys
import time
from pathlib import Path

import duckdb

CAMINHO_BANCO = Path(__file__).resolve().parent / "data" / "olympics.duckdb"
URL = "http://localhost:4213"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    if not CAMINHO_BANCO.is_file():
        print(
            f"Banco não encontrado em {CAMINHO_BANCO}.\n"
            "Rode a ingestão antes: uv run python -m pipeline.ingestao",
            file=sys.stderr,
        )
        sys.exit(1)

    con = duckdb.connect(str(CAMINHO_BANCO), read_only=True)
    try:
        con.execute("INSTALL ui")
        con.execute("LOAD ui")
        con.execute("CALL start_ui()").fetchall()
        print(f"DuckDB UI em {URL} (somente leitura). Ctrl+C para encerrar.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        con.close()
    print("UI encerrada; banco liberado.")


if __name__ == "__main__":
    main()

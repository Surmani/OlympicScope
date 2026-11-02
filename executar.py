"""Reconstrói o banco do zero: ingestão → refined → marts. Unidade 6.1.

Como rodar: ``uv run python executar.py`` (feche o ``ui.py`` antes).

Regras e motivos
----------------

- Apaga ``data/olympics.duckdb`` (e o ``.wal``, se houver) antes de começar.
  Motivo: "do zero" de verdade. O ``CREATE OR REPLACE`` de cada etapa não
  remove tabelas que deixaram de existir (ex.: um mart renomeado deixaria a
  versão antiga no banco). Só o banco é apagado: ele é um arquivo gerado, e
  ``raw/`` nunca é tocado.
- Confere os arquivos de ``raw/`` ANTES de apagar o banco.
  Motivo: se faltar um CSV, o banco que já existia continua lá, em vez de
  sumir e não ser recriado.
- Se o banco estiver aberto por outro programa (o ``ui.py`` trava o arquivo),
  avisa em ``stderr`` e encerra com ``sys.exit(1)`` sem apagar nada.
- Roda as três etapas em ordem, chamando o ``main()`` de cada uma, que
  imprime as contagens lidas do banco. A refined roda as 12 verificações.
- Se uma etapa falhar, para ali, diz qual foi e termina com o mesmo código de
  erro (as etapas seguintes não rodam sobre dado inconsistente).
- ``stdout`` reconfigurado para UTF-8.

Critérios de aceite (verificados em ``tests/test_executar.py``)
--------------------------------------------------------------

1. Com ``raw/`` completo, cria as tabelas raw, refined e marts e imprime as
   três etapas e ``verificações: 12 de 12 ok``.
2. Uma tabela que existia antes e não é criada por nenhuma etapa some.
3. Faltando um arquivo em ``raw/``, encerra com código 1 e o banco que
   existia não é apagado.
4. Com o banco travado por outro programa, encerra com código 1, avisa para
   fechar o ``ui.py`` e não roda nenhuma etapa.
5. Uma etapa que falha interrompe as seguintes e devolve o código de erro.
"""

import sys

from pipeline import db, ingestao, marts, refined

ETAPAS = (
    ("Ingestão (raw/ → schema raw)", ingestao.main),
    ("Refined (schema raw → schema refined)", refined.main),
    ("Marts (schema refined → schema marts)", marts.main),
)


def apagar_banco() -> None:
    """Apaga o banco e o .wal; encerra com código 1 se estiverem travados."""
    # db.CAMINHO_BANCO é lido na hora da chamada, o que permite aos testes
    # apontá-lo para um arquivo temporário.
    for arquivo in (
        db.CAMINHO_BANCO,
        db.CAMINHO_BANCO.with_name(db.CAMINHO_BANCO.name + ".wal"),
    ):
        try:
            arquivo.unlink(missing_ok=True)
        except PermissionError:
            print(
                f"Não foi possível apagar {arquivo}: ele está aberto em outro "
                "programa. Feche o ui.py (Ctrl+C) e rode de novo.",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ingestao.validar_arquivos(db.PASTA_RAW)
    apagar_banco()

    for numero, (nome, etapa) in enumerate(ETAPAS, start=1):
        print(f"\n== {numero}/{len(ETAPAS)} {nome} ==")
        try:
            etapa()
        except SystemExit as erro:
            if erro.code not in (0, None):
                print(
                    f"\nParou na etapa {numero}/{len(ETAPAS)}: {nome}.", file=sys.stderr
                )
            raise

    print(f"\nPronto: banco recriado do zero em {db.CAMINHO_BANCO}.")


if __name__ == "__main__":
    main()

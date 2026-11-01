"""Ingestão: arquivos de raw/ → schema raw do DuckDB.

Como rodar: ``uv run python -m pipeline.ingestao``
(rodar ``python pipeline/ingestao.py`` direto quebra o ``from pipeline import db``).

Unidade 2.1 — validação dos arquivos de origem
=============================================

Antes de abrir o banco, a ingestão confere se todos os arquivos de origem
existem em ``PASTA_RAW``.

Regras e motivos
----------------

- A lista de arquivos esperados fica aqui (``ARQUIVOS``), não em ``db.py``.
  Motivo: ``db.py`` não conhece nome de tabela nem de arquivo; quem sabe o que
  precisa ser ingerido é a ingestão.
- Se faltar qualquer arquivo, nada é ingerido: o programa lista todos os que
  faltam (não só o primeiro), diz em que pasta procurou e encerra com
  ``sys.exit(1)``.
  Motivo: ingerir uma tabela de duas em silêncio produz indicadores errados
  que parecem certos. Listar todos de uma vez evita corrigir um, rodar de
  novo e descobrir o próximo.
- A mensagem de erro vai para ``stderr``.
  Motivo: ``stdout`` fica reservado para as contagens da ingestão.
- "Existir" significa ser um arquivo (``Path.is_file()``); uma pasta com o
  nome do arquivo conta como faltando.
  Motivo: uma pasta com o nome certo passaria na checagem e só quebraria
  depois, na leitura, com um erro menos claro.
- A validação confere só a existência. Conteúdo, cabeçalho e tamanho não
  são verificados aqui.
  Motivo: a spec pede apenas a checagem de existência; o que foi lido é
  conferido pelas contagens gravadas no banco.

Critérios de aceite (verificados em ``tests/test_ingestao.py``)
--------------------------------------------------------------

1. Com todos os arquivos presentes, ``arquivos_faltando`` devolve lista vazia
   e ``validar_arquivos`` retorna sem encerrar e sem imprimir nada.
2. Faltando um arquivo, ``arquivos_faltando`` devolve exatamente esse nome.
3. Faltando todos, ``arquivos_faltando`` devolve todos, na ordem de ``ARQUIVOS``.
4. Uma pasta com o nome de um arquivo esperado conta como faltando.
5. Faltando algum arquivo, ``validar_arquivos`` encerra com código 1 e
   escreve em ``stderr`` o nome de cada arquivo faltante e a pasta procurada;
   ``stdout`` fica vazio.

Unidade 2.2 — leitura dos CSVs como texto e criação das tabelas raw
===================================================================

Cada arquivo de ``ARQUIVOS`` vira uma tabela no schema ``raw``, com o nome do
arquivo sem extensão (``athlete_events.csv`` → ``raw.athlete_events``).

Regras e motivos
----------------

- Nenhuma limpeza: nenhuma conversão de tipo, nenhuma linha descartada ou
  deduplicada, nenhum nome de coluna alterado, nenhum valor corrigido.
  Motivo: a fronteira entre "o dado que chegou" e "o dado que eu decidi"
  fica na passagem de raw para refined.
- Leitura com ``dtype=str``: todas as colunas viram VARCHAR.
  Motivo: conversão de tipo é decisão, e decisões são registradas na refined.
- Leitura com ``keep_default_na=False``: o texto ``NA`` continua sendo o
  texto ``NA``.
  Motivo: neste dataset a ausência vem escrita como ``NA``; transformá-la em
  nulo na leitura seria uma normalização escondida dentro da raw.
- ``encoding="utf-8"`` declarado, nunca adivinhado.
  Motivo: adivinhar encoding pode trocar acentos em silêncio.
- A validação dos arquivos acontece antes de abrir o banco.
  Motivo: se faltar um arquivo, nem o arquivo do banco é criado.
- Idempotente: ``CREATE OR REPLACE TABLE`` (via ``db.gravar``).
  Motivo: rodar duas vezes tem que dar o mesmo resultado.
- Ao final, uma linha por tabela com a contagem lida do banco e uma linha
  com o total, milhar separado por ponto.
  Motivo: a contagem na tela tem que ser a do que foi gravado, não a do que
  estava na memória.
- ``stdout`` reconfigurado para UTF-8 dentro do ``main()``, não na importação.
  Motivo: no Windows os acentos saem embaralhados por padrão; e importar o
  módulo (como fazem os testes e o futuro ``executar.py``) não deve mexer
  no terminal de quem importa.
- A conexão é fechada num ``finally``, mesmo se a leitura falhar no meio.
  Motivo: uma conexão esquecida aberta trava o arquivo ``.duckdb``.

Critérios de aceite (verificados em ``tests/test_ingestao.py``)
--------------------------------------------------------------

6. O texto ``NA`` chega ao banco como o texto ``NA``, não como NULL.
7. Todas as colunas das tabelas raw são VARCHAR, inclusive as só numéricas.
8. Os nomes das colunas são exatamente os do cabeçalho do CSV.
9. Rodar a ingestão duas vezes imprime exatamente a mesma coisa e não
   duplica linhas.
10. Faltando um arquivo, o programa encerra com código 1 e o arquivo do
    banco não é criado.
11. ``formatar_milhar(271116)`` devolve ``"271.116"``.
"""

import sys
from pathlib import Path

import pandas as pd

from pipeline import db

ARQUIVOS = ("athlete_events.csv", "noc_regions.csv")


def arquivos_faltando(pasta: Path) -> list[str]:
    """Devolve os nomes de ARQUIVOS que não existem como arquivo em pasta."""
    return [nome for nome in ARQUIVOS if not (pasta / nome).is_file()]


def validar_arquivos(pasta: Path) -> None:
    """Encerra com sys.exit(1) se faltar algum arquivo de origem em pasta."""
    faltando = arquivos_faltando(pasta)
    if not faltando:
        return

    linhas = [f"Arquivos de origem não encontrados em {pasta}:"]
    linhas += [f"  - {nome}" for nome in faltando]
    linhas.append("Nada foi ingerido.")
    print("\n".join(linhas), file=sys.stderr)
    sys.exit(1)


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê o CSV com todas as colunas como texto e o texto NA preservado."""
    return pd.read_csv(caminho, dtype=str, keep_default_na=False, encoding="utf-8")


def formatar_milhar(numero: int) -> str:
    """Formata um inteiro com ponto como separador de milhar."""
    return f"{numero:,}".replace(",", ".")


def ingerir() -> dict[str, int]:
    """Valida os arquivos, grava cada um no schema raw e devolve as contagens do banco."""
    # db.PASTA_RAW é lido na hora da chamada, o que permite aos testes
    # apontá-lo para uma pasta temporária.
    validar_arquivos(db.PASTA_RAW)

    contagens = {}
    con = db.conectar()
    try:
        db.criar_schema(con, "raw")
        for nome in ARQUIVOS:
            tabela = Path(nome).stem
            df = ler_csv(db.PASTA_RAW / nome)
            contagens[f"raw.{tabela}"] = db.gravar(con, df, "raw", tabela)
    finally:
        con.close()
    return contagens


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    contagens = ingerir()
    for tabela, linhas in contagens.items():
        print(f"{tabela}: {formatar_milhar(linhas)} linhas")
    print(f"Total: {formatar_milhar(sum(contagens.values()))} linhas")


if __name__ == "__main__":
    main()

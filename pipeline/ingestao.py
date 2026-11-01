"""Ingestão: arquivos de raw/ → schema raw do DuckDB.

Unidade 2.1 — validação dos arquivos de origem.

Antes de abrir o banco, a ingestão confere se todos os arquivos de origem
existem em ``PASTA_RAW``. A leitura dos CSVs e a gravação no banco ficam para
a unidade 2.2.

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
"""

import sys
from pathlib import Path

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

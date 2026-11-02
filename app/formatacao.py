"""Formatação de valores no padrão brasileiro — unidade 5.1.

Só exibição: banco, refined e marts continuam em centímetros e quilogramas,
com ponto decimal. Estas funções transformam o valor em texto para a tela.

Regras e motivos
----------------

- Milhar com ponto e decimal com vírgula (``1.019``, ``45,03``).
  Motivo: padrão brasileiro, pedido na spec (seção STREAMLIT).
- Altura exibida em metros (``175`` cm → ``"1,75 m"``) e peso em quilogramas
  com 2 casas (``"63,50 kg"``).
  Motivo: o dado já é métrico (cm e kg, conferido na unidade 3.3); no Brasil
  a altura costuma ser dita em metros. A conversão acontece só aqui, na hora
  de mostrar, nunca antes de uma conta.
- Arredondamento "meio para cima" (``0,125`` → ``0,13``), com ``Decimal``.
  Motivo: é o arredondamento que as pessoas esperam; o padrão do Python
  (meio para o par) mostraria ``0,12``.
- Valor ausente (``None``, ``NaN`` ou ``pd.NA``) vira ``"—"``.
  Motivo: deixar claro que não há dado, sem confundir com zero.

Critérios de aceite (verificados em ``tests/test_app_formatacao.py``)
-------------------------------------------------------------------

1. ``formatar_inteiro(1019)`` → ``"1.019"``; ``formatar_decimal(1234.5)`` →
   ``"1.234,50"``.
2. ``formatar_percentual(45.03)`` → ``"45,03%"``.
3. ``formatar_altura(175)`` → ``"1,75 m"``; ``formatar_peso(Decimal("63.5"))``
   → ``"63,50 kg"``; ``formatar_idade(24.5)`` → ``"24,50 anos"``.
4. Ausência vira ``"—"``; ``0,125`` arredonda para ``"0,13"``.
5. ``formatar_ano(2016)`` → ``"2016"`` (anos e posições sem separador de milhar).
"""

from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

AUSENTE = "—"


def _ausente(valor) -> bool:
    # pd.isna cobre None, NaN e pd.NA (o DuckDB pode devolver qualquer um).
    return valor is None or bool(pd.isna(valor))


def _para_brasileiro(texto: str) -> str:
    """Troca o formato americano (1,234.56) pelo brasileiro (1.234,56)."""
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_inteiro(valor) -> str:
    if _ausente(valor):
        return AUSENTE
    return _para_brasileiro(f"{int(valor):,}")


def formatar_ano(valor) -> str:
    """Ano ou posição de ranking: inteiro sem separador de milhar (2016, não 2.016)."""
    if _ausente(valor):
        return AUSENTE
    return str(int(valor))


def formatar_decimal(valor, casas: int = 2) -> str:
    if _ausente(valor):
        return AUSENTE
    arredondado = Decimal(str(valor)).quantize(
        Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP
    )
    return _para_brasileiro(f"{arredondado:,.{casas}f}")


def formatar_percentual(valor) -> str:
    if _ausente(valor):
        return AUSENTE
    return f"{formatar_decimal(valor)}%"


def formatar_altura(centimetros) -> str:
    if _ausente(centimetros):
        return AUSENTE
    return f"{formatar_decimal(Decimal(str(centimetros)) / 100)} m"


def formatar_peso(quilogramas) -> str:
    if _ausente(quilogramas):
        return AUSENTE
    return f"{formatar_decimal(quilogramas)} kg"


def formatar_idade(anos) -> str:
    if _ausente(anos):
        return AUSENTE
    return f"{formatar_decimal(anos)} anos"


def formatar_tabela(df, formatos: dict):
    """Devolve uma cópia do DataFrame com as colunas indicadas virando texto.

    ``formatos`` liga o nome da coluna à função de formatação. As demais
    colunas ficam como estão.
    """
    tabela = df.copy()
    for coluna, funcao in formatos.items():
        tabela[coluna] = tabela[coluna].map(funcao).astype(object)
    return tabela

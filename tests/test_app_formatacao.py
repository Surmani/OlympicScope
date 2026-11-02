"""Testes de app/formatacao.py (padrão brasileiro, só exibição)."""

from decimal import Decimal

import pandas as pd
import pytest

from app import formatacao as f


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(0, "0"), (19, "19"), (1019, "1.019"), (271116, "271.116"), (None, "—")],
)
def test_formatar_inteiro(valor, esperado):
    assert f.formatar_inteiro(valor) == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (45.03, "45,03"),
        (1234.5, "1.234,50"),
        (Decimal("63.5"), "63,50"),
        (0.125, "0,13"),  # meio para cima, não meio para o par
        (2.675, "2,68"),
        (float("nan"), "—"),
        (pd.NA, "—"),
    ],
)
def test_formatar_decimal(valor, esperado):
    assert f.formatar_decimal(valor) == esperado


def test_formatar_decimal_com_uma_casa():
    assert f.formatar_decimal(21.666, casas=1) == "21,7"


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(2016, "2016"), (1896.0, "1896"), (1, "1"), (None, "—"), (float("nan"), "—")],
)
def test_formatar_ano_sem_separador_de_milhar(valor, esperado):
    assert f.formatar_ano(valor) == esperado


def test_formatar_percentual():
    assert f.formatar_percentual(45.03) == "45,03%"
    assert f.formatar_percentual(Decimal("0.00")) == "0,00%"
    assert f.formatar_percentual(None) == "—"


@pytest.mark.parametrize(
    ("centimetros", "esperado"),
    [(175, "1,75 m"), (Decimal("194.87"), "1,95 m"), (160, "1,60 m"), (None, "—")],
)
def test_formatar_altura_em_metros(centimetros, esperado):
    assert f.formatar_altura(centimetros) == esperado


def test_formatar_peso_e_idade():
    assert f.formatar_peso(Decimal("63.5")) == "63,50 kg"
    assert f.formatar_peso(102) == "102,00 kg"
    assert f.formatar_idade(24.5) == "24,50 anos"
    assert f.formatar_peso(None) == "—"


def test_formatar_tabela_so_muda_as_colunas_indicadas():
    df = pd.DataFrame({"noc": ["BRA", "USA"], "atletas": [462, 1019]})
    tabela = f.formatar_tabela(df, {"atletas": f.formatar_inteiro})

    assert tabela.to_dict("list") == {
        "noc": ["BRA", "USA"],
        "atletas": ["462", "1.019"],
    }
    assert df["atletas"].tolist() == [462, 1019]  # o original não muda

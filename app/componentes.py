"""Componentes de tela usados por mais de uma página — unidade 5.1.

Só apresentação: escolhas de filtro e tabelas formatadas. Os dados vêm das
consultas de ``consultas.py``, via cache de ``dados.py``.
"""

import streamlit as st

import consultas
from dados import carregar
from formatacao import formatar_tabela


def mostrar_tabela(df, formatos: dict, nomes: dict) -> None:
    """Tabela com as colunas formatadas no padrão brasileiro e nomes em português."""
    tabela = formatar_tabela(df, formatos).rename(columns=nomes)
    st.dataframe(tabela, hide_index=True, width="stretch")


def escolher_pais(season: str, chave: str) -> str:
    """Caixa de seleção de NOC (padrão: BRA), mostrando a região ao lado."""
    lista = carregar(consultas.paises(season))
    rotulos = dict(zip(lista["noc"], lista["region"].fillna("sem região")))
    nocs = list(rotulos)
    padrao = nocs.index("BRA") if "BRA" in nocs else 0
    return st.selectbox(
        "País (NOC)",
        nocs,
        index=padrao,
        format_func=lambda noc: f"{noc} — {rotulos[noc]}",
        key=chave,
    )


def escolher_edicao(season: str, chave: str) -> str:
    """Caixa de seleção de edição (padrão: a mais recente), com a cidade-sede."""
    lista = carregar(consultas.edicoes(season))
    cidades = dict(zip(lista["games_id"], lista["city"]))
    return st.selectbox(
        "Edição",
        list(cidades),
        format_func=lambda games_id: f"{games_id} — {cidades[games_id]}",
        key=chave,
    )

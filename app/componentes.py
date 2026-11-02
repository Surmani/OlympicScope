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


def escolher_pais(season: str, chave: str, so_com_medalha_padrao: bool = False):
    """Caixa de seleção de NOC (padrão: BRA), com a região ao lado.

    Uma caixa de marcar logo acima permite listar só os países que já ganharam
    medalha na temporada (ex.: no Inverno o Brasil nunca ganhou e sai da
    lista). Devolve None se nenhum país sobrar.
    """
    so_com_medalha = st.checkbox(
        "Listar só países que já ganharam medalha nesta temporada",
        value=so_com_medalha_padrao,
        key=f"{chave}_so_com_medalha",
    )
    consulta = (
        consultas.paises_com_medalha(season)
        if so_com_medalha
        else consultas.paises(season)
    )
    lista = carregar(consulta)
    if lista.empty:
        st.warning("Nenhum país para mostrar com esse filtro.")
        return None
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

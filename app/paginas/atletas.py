"""Página Atletas — marts 06, 13 e 14 (unidade 5.2).

Só exibe o que vem das consultas (``consultas.py``); nenhuma conta aqui.
"""

import streamlit as st

import consultas
from componentes import mostrar_tabela
from dados import carregar
from formatacao import (
    formatar_altura,
    formatar_ano,
    formatar_idade,
    formatar_inteiro,
    formatar_peso,
)


def perfil_por_modalidade(season):
    st.subheader("Perfil médio dos atletas por modalidade")
    st.caption(
        "Idade, altura e peso médios de todas as edições do período. Cada atleta "
        'entra uma vez por edição em cada modalidade. As colunas "n" dizem sobre '
        "quantos atletas × edição cada média foi calculada; o corte esconde médias "
        "com poucos dados."
    )
    coluna_sexo, coluna_corte = st.columns(2)
    with coluna_sexo:
        sexo = st.radio("Sexo", ["F", "M"], horizontal=True, key="sexo_modalidade")
    with coluna_corte:
        minimo = st.slider(
            "Mínimo de atletas na média de altura", 1, 100, 10, key="corte_modalidade"
        )
    df = carregar(consultas.perfil_modalidades(season, sexo, minimo))
    st.bar_chart(
        df.head(10),
        x="sport",
        y="altura_media",
        horizontal=True,
        sort="-altura_media",
        x_label="Altura média (cm)",
        y_label="",
    )
    mostrar_tabela(
        df,
        {
            "idade_media": formatar_idade,
            "altura_media": formatar_altura,
            "peso_media": formatar_peso,
            "n_idade": formatar_inteiro,
            "n_altura": formatar_inteiro,
            "n_peso": formatar_inteiro,
        },
        {
            "sport": "Modalidade",
            "idade_media": "Idade média",
            "altura_media": "Altura média",
            "peso_media": "Peso médio",
            "n_idade": "n (idade)",
            "n_altura": "n (altura)",
            "n_peso": "n (peso)",
        },
    )


def longevidade():
    st.subheader("Atletas com mais edições disputadas")
    st.caption(
        "Soma Verão e Inverno: é a carreira olímpica inteira. Só atletas com 2 "
        "edições ou mais. Empate em edições é desfeito pelos anos de carreira "
        "(último ano − primeiro). Quem defendeu mais de um país aparece com todos "
        "os NOCs."
    )
    limite = st.slider(
        "Mostrar até a posição", 10, 100, 20, step=10, key="limite_longevidade"
    )
    df = carregar(consultas.longevidade(limite))
    mostrar_tabela(
        df,
        {
            "ranking": formatar_ano,
            "edicoes": formatar_inteiro,
            "primeiro_ano": formatar_ano,
            "ultimo_ano": formatar_ano,
            "anos_de_carreira": formatar_inteiro,
        },
        {
            "ranking": "Posição",
            "name": "Atleta",
            "sex": "Sexo",
            "noc": "NOC",
            "edicoes": "Edições",
            "primeiro_ano": "Primeiro ano",
            "ultimo_ano": "Último ano",
            "anos_de_carreira": "Anos de carreira",
        },
    )


def mais_jovens_e_mais_velhos(season):
    st.subheader("Medalhistas mais jovens e mais velhos")
    st.caption(
        "Menor e maior idade entre os medalhistas da modalidade, no período dos "
        "dados. Todos os empatados aparecem. Medalhas sem idade registrada ficam "
        "de fora."
    )
    lista = carregar(consultas.modalidades(season))["sport"].tolist()
    padrao = lista.index("Swimming") if "Swimming" in lista else 0
    sport = st.selectbox("Modalidade", lista, index=padrao, key="modalidade_extremos")
    df = carregar(consultas.extremos(sport, season))
    mostrar_tabela(
        df,
        {"idade": formatar_ano, "medalhas": formatar_inteiro},
        {
            "extremo": "Extremo",
            "idade": "Idade",
            "name": "Atleta",
            "sex": "Sexo",
            "noc": "NOC",
            "games_id": "Edição",
            "medalhas": "Medalhas nessa idade",
            "provas": "Provas",
        },
    )


def pagina():
    season = st.session_state["season"]
    nome_temporada = st.session_state["nome_temporada"]
    st.header(f"Atletas — Jogos de {nome_temporada}")
    aba_perfil, aba_longevidade, aba_extremos = st.tabs(
        ["Perfil por modalidade", "Longevidade", "Mais jovens e mais velhos"]
    )
    with aba_perfil:
        perfil_por_modalidade(season)
    with aba_longevidade:
        longevidade()
    with aba_extremos:
        mais_jovens_e_mais_velhos(season)

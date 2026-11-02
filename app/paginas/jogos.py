"""Página Os Jogos — marts 03, 04, 05 e 15 (unidade 5.2).

Só exibe o que vem das consultas (``consultas.py``); nenhuma conta aqui.
"""

import streamlit as st

import consultas
from componentes import mostrar_tabela
from dados import carregar
from formatacao import formatar_ano, formatar_inteiro, formatar_percentual

INDICADORES_EVOLUCAO = {
    "Atletas": "atletas",
    "Países": "paises",
    "Modalidades": "modalidades",
    "Provas": "provas",
}

INDICADORES_MODALIDADE = {
    "Participações": "participacoes",
    "Atletas": "atletas",
    "Provas": "provas",
    "Medalhas conquistadas": "medalhas_conquistadas",
}


def evolucao(season):
    st.subheader("Como os Jogos cresceram")
    st.caption(
        "Atletas (cada um conta uma vez por edição), países (NOCs), modalidades e "
        "provas em cada edição. Em 1956, o hipismo foi em Stockholm e o resto em "
        "Melbourne."
    )
    nome = st.radio(
        "Indicador",
        list(INDICADORES_EVOLUCAO),
        horizontal=True,
        key="indicador_evolucao",
    )
    df = carregar(consultas.evolucao(season))
    st.line_chart(
        df, x="year", y=INDICADORES_EVOLUCAO[nome], x_label="Ano", y_label=nome
    )
    mostrar_tabela(
        df,
        {
            "year": formatar_ano,
            "atletas": formatar_inteiro,
            "paises": formatar_inteiro,
            "modalidades": formatar_inteiro,
            "provas": formatar_inteiro,
        },
        {
            "games_id": "Edição",
            "year": "Ano",
            "city": "Cidade-sede",
            "atletas": "Atletas",
            "paises": "Países",
            "modalidades": "Modalidades",
            "provas": "Provas",
        },
    )


def participacao_por_genero(season):
    st.subheader("Participação de mulheres e homens")
    st.caption(
        "Porcentagem de atletas de cada sexo por edição. Em 1896 não houve "
        "mulheres: a linha aparece com 0%."
    )
    df = carregar(consultas.participacao_genero(season))
    st.line_chart(
        df,
        x="year",
        y="percentual_atletas",
        color="sex",
        x_label="Ano",
        y_label="% dos atletas",
    )
    mostrar_tabela(
        df,
        {
            "year": formatar_ano,
            "atletas": formatar_inteiro,
            "percentual_atletas": formatar_percentual,
        },
        {
            "games_id": "Edição",
            "year": "Ano",
            "sex": "Sexo",
            "atletas": "Atletas",
            "percentual_atletas": "% dos atletas",
        },
    )


def tamanho_das_modalidades(season):
    st.subheader("Tamanho de cada modalidade")
    st.caption(
        "Somando todas as edições do período. Participações = atleta × prova × "
        "edição. **Medalhas conquistadas** conta 1 por prova (um time campeão soma "
        "1); **registros de medalhistas** conta 1 por atleta premiado."
    )
    nome = st.radio(
        "Ordenar o gráfico por",
        list(INDICADORES_MODALIDADE),
        horizontal=True,
        key="indicador_modalidade",
    )
    coluna = INDICADORES_MODALIDADE[nome]
    df = carregar(consultas.desempenho_modalidades(season))
    st.bar_chart(
        df.sort_values(coluna, ascending=False).head(10),
        x="sport",
        y=coluna,
        horizontal=True,
        sort=f"-{coluna}",
        x_label=nome,
        y_label="",
    )
    mostrar_tabela(
        df,
        {
            "participacoes": formatar_inteiro,
            "atletas": formatar_inteiro,
            "provas": formatar_inteiro,
            "medalhas_conquistadas": formatar_inteiro,
            "registros_medalhistas": formatar_inteiro,
        },
        {
            "sport": "Modalidade",
            "participacoes": "Participações",
            "atletas": "Atletas",
            "provas": "Provas",
            "medalhas_conquistadas": "Medalhas conquistadas",
            "registros_medalhistas": "Registros de medalhistas",
        },
    )


def programa_olimpico(season, nome_temporada):
    ultima = "2016" if season == "Summer" else "2014"
    st.subheader("Quando cada modalidade entrou e saiu")
    st.caption(
        f'"Na última edição do dataset" quer dizer {ultima} ({nome_temporada}), '
        "não as edições mais recentes dos Jogos, que não estão nos dados. "
        "Ausências = edições entre a primeira e a última em que a modalidade "
        "ficou de fora."
    )
    df = carregar(consultas.programa(season))
    mostrar_tabela(
        df,
        {
            "primeiro_ano": formatar_ano,
            "ultimo_ano": formatar_ano,
            "edicoes": formatar_inteiro,
            "ausencias": formatar_inteiro,
            "no_programa_atual": lambda v: "Sim" if v else "Não",
        },
        {
            "sport": "Modalidade",
            "primeira_edicao": "Primeira edição",
            "primeiro_ano": "Primeiro ano",
            "ultima_edicao": "Última edição",
            "ultimo_ano": "Último ano",
            "edicoes": "Edições",
            "ausencias": "Ausências",
            "no_programa_atual": f"Em {ultima}?",
        },
    )


def pagina():
    season = st.session_state["season"]
    nome_temporada = st.session_state["nome_temporada"]
    st.header(f"Os Jogos — {nome_temporada}")
    aba_evolucao, aba_genero, aba_modalidades, aba_programa = st.tabs(
        [
            "Evolução",
            "Mulheres e homens",
            "Tamanho das modalidades",
            "Programa olímpico",
        ]
    )
    with aba_evolucao:
        evolucao(season)
    with aba_genero:
        participacao_por_genero(season)
    with aba_modalidades:
        tamanho_das_modalidades(season)
    with aba_programa:
        programa_olimpico(season, nome_temporada)

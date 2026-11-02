"""Página Países — marts 09, 10, 12 e 07 (unidade 5.1).

Só exibe o que vem das consultas (``consultas.py``); nenhuma conta aqui.
"""

import streamlit as st

import consultas
from componentes import escolher_edicao, escolher_pais, mostrar_tabela
from dados import carregar
from formatacao import (
    formatar_altura,
    formatar_ano,
    formatar_decimal,
    formatar_idade,
    formatar_inteiro,
    formatar_percentual,
    formatar_peso,
)


def estreias(season, nome_temporada):
    st.subheader(f"Estreia e primeira medalha — Jogos de {nome_temporada}")
    st.caption(
        "Primeira edição disputada, primeira medalha e primeiro ouro de cada país, "
        'dentro do período dos dados. "Edições até a 1ª medalha" conta a '
        "edição da medalha (1 = ganhou na estreia). — = ainda não aconteceu até "
        "2016 (Verão) ou 2014 (Inverno)."
    )
    df = carregar(consultas.estreias(season))
    mostrar_tabela(
        df,
        {
            "ano_primeira_edicao": formatar_ano,
            "ano_primeira_medalha": formatar_ano,
            "edicoes_ate_primeira_medalha": formatar_ano,
            "ano_primeiro_ouro": formatar_ano,
            "primeira_medalha": lambda v: v if isinstance(v, str) else "—",
            "primeiro_ouro": lambda v: v if isinstance(v, str) else "—",
        },
        {
            "noc": "NOC",
            "region": "Região",
            "primeira_edicao": "Estreia",
            "ano_primeira_edicao": "Ano da estreia",
            "primeira_medalha": "1ª medalha",
            "ano_primeira_medalha": "Ano da 1ª medalha",
            "edicoes_ate_primeira_medalha": "Edições até a 1ª medalha",
            "primeiro_ouro": "1º ouro",
            "ano_primeiro_ouro": "Ano do 1º ouro",
        },
    )


def eficiencia(season):
    st.subheader("Medalhas para cada 100 atletas enviados")
    st.caption(
        "Medalhas conquistadas ÷ tamanho da delegação × 100. Delegações muito "
        "pequenas distorcem a taxa (em 1896, a Austrália mandou 1 atleta e ganhou "
        "3 medalhas = 300 por 100); por isso o corte de delegação mínima."
    )
    games_id = escolher_edicao(season, "edicao_eficiencia")
    minimo = st.slider("Delegação mínima (atletas)", 1, 100, 10)
    df = carregar(consultas.eficiencia(games_id, minimo))
    st.bar_chart(
        df.head(10),
        x="noc",
        y="medalhas_por_100_atletas",
        horizontal=True,
        sort="-medalhas_por_100_atletas",
        x_label="Medalhas por 100 atletas",
        y_label="",
    )
    mostrar_tabela(
        df,
        {
            "atletas": formatar_inteiro,
            "medalhas_conquistadas": formatar_inteiro,
            "medalhas_por_100_atletas": formatar_decimal,
        },
        {
            "noc": "NOC",
            "region": "Região",
            "atletas": "Atletas na delegação",
            "medalhas_conquistadas": "Medalhas conquistadas",
            "medalhas_por_100_atletas": "Medalhas por 100 atletas",
        },
    )


def mulheres_na_delegacao(season):
    st.subheader("Participação de mulheres na delegação")
    st.caption(
        "Porcentagem de mulheres entre os atletas do país em cada edição. "
        "Cada atleta conta uma vez por edição, mesmo disputando várias provas."
    )
    noc = escolher_pais(season, "pais_genero")
    df = carregar(consultas.genero_pais(noc, season))
    st.line_chart(
        df, x="year", y="percentual_mulheres", x_label="Ano", y_label="% de mulheres"
    )
    mostrar_tabela(
        df,
        {
            "year": formatar_ano,
            "atletas_f": formatar_inteiro,
            "atletas_m": formatar_inteiro,
            "atletas": formatar_inteiro,
            "percentual_mulheres": formatar_percentual,
        },
        {
            "games_id": "Edição",
            "year": "Ano",
            "atletas_f": "Mulheres",
            "atletas_m": "Homens",
            "atletas": "Total",
            "percentual_mulheres": "% de mulheres",
        },
    )


def perfil_por_pais(season):
    st.subheader("Perfil médio dos atletas por país")
    st.caption(
        "Idade, altura e peso médios de todas as edições do período. Cada atleta "
        'entra uma vez por edição. As colunas "n" dizem sobre quantos atletas × '
        "edição cada média foi calculada; o corte esconde médias com poucos dados."
    )
    coluna_sexo, coluna_corte = st.columns(2)
    with coluna_sexo:
        sexo = st.radio("Sexo", ["F", "M"], horizontal=True, key="sexo_perfil")
    with coluna_corte:
        minimo = st.slider("Mínimo de atletas na média de altura", 1, 100, 10)
    df = carregar(consultas.perfil_paises(season, sexo, minimo))
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
            "noc": "NOC",
            "region": "Região",
            "idade_media": "Idade média",
            "altura_media": "Altura média",
            "peso_media": "Peso médio",
            "n_idade": "n (idade)",
            "n_altura": "n (altura)",
            "n_peso": "n (peso)",
        },
    )


def pagina():
    season = st.session_state["season"]
    nome_temporada = st.session_state["nome_temporada"]
    st.header(f"Países — Jogos de {nome_temporada}")
    aba_estreias, aba_eficiencia, aba_genero, aba_perfil = st.tabs(
        ["Estreias", "Eficiência", "Mulheres na delegação", "Perfil dos atletas"]
    )
    with aba_estreias:
        estreias(season, nome_temporada)
    with aba_eficiencia:
        eficiencia(season)
    with aba_genero:
        mulheres_na_delegacao(season)
    with aba_perfil:
        perfil_por_pais(season)

"""Página Medalhas — marts 01, 02, 08 e 11 (unidade 5.1).

Só exibe o que vem das consultas (``consultas.py``); nenhuma conta aqui.
"""

import streamlit as st

import consultas
from componentes import escolher_edicao, escolher_pais, mostrar_tabela
from dados import carregar
from formatacao import formatar_ano, formatar_inteiro, formatar_percentual

CORES_MEDALHAS = ["#D4AF37", "#A8A9AD", "#CD7F32"]  # ouro, prata, bronze

EXPLICACAO_CONTAGEM = (
    "**Medalhas conquistadas** conta 1 por prova: um time de basquete campeão "
    "soma 1 ouro. **Registros de medalhistas** conta 1 por atleta premiado: o "
    "mesmo time soma 12."
)

COLUNAS_QUADRO = {
    "ranking_edicao": "Posição",
    "ranking_historico": "Posição",
    "ranking_modalidade": "Posição",
    "noc": "NOC",
    "region": "Região",
    "ouro": "Ouro",
    "prata": "Prata",
    "bronze": "Bronze",
    "medalhas_conquistadas": "Medalhas conquistadas",
    "registros_medalhistas": "Registros de medalhistas",
    "edicoes_disputadas": "Edições disputadas",
    "percentual_medalhas": "% das medalhas da modalidade",
}

FORMATOS_QUADRO = {
    "ouro": formatar_inteiro,
    "prata": formatar_inteiro,
    "bronze": formatar_inteiro,
    "medalhas_conquistadas": formatar_inteiro,
    "registros_medalhistas": formatar_inteiro,
}


def _grafico_medalhas(df, eixo):
    """Barras empilhadas de ouro, prata e bronze das 10 primeiras linhas."""
    st.bar_chart(
        df.head(10),
        x=eixo,
        y=["ouro", "prata", "bronze"],
        color=CORES_MEDALHAS,
        horizontal=True,
        sort=False,
        x_label="Medalhas conquistadas",
        y_label="",
    )


def quadro_por_edicao(season):
    st.subheader("Quadro de medalhas por edição")
    st.caption(
        "Posição pelo critério do COI: mais ouros; empate, mais pratas; empate, "
        "mais bronzes. Países empatados dividem a posição. " + EXPLICACAO_CONTAGEM
    )
    games_id = escolher_edicao(season, "edicao_quadro")
    df = carregar(consultas.quadro_edicao(games_id))
    _grafico_medalhas(df, "noc")
    mostrar_tabela(
        df, {"ranking_edicao": formatar_ano, **FORMATOS_QUADRO}, COLUNAS_QUADRO
    )

    st.subheader("Um país ao longo das edições")
    noc = escolher_pais(season, "pais_evolucao")
    historico = carregar(consultas.pais_por_edicao(noc, season))
    st.line_chart(
        historico,
        x="year",
        y="medalhas_conquistadas",
        x_label="Ano",
        y_label="Medalhas conquistadas",
    )
    mostrar_tabela(
        historico,
        {"year": formatar_ano, "ranking_edicao": formatar_ano, **FORMATOS_QUADRO},
        {**COLUNAS_QUADRO, "games_id": "Edição", "year": "Ano"},
    )


def quadro_historico(season, nome_temporada):
    st.subheader(f"Quadro histórico — Jogos de {nome_temporada}")
    st.caption(
        "Soma de todas as edições do período dos dados (até 2016 no Verão, 2014 "
        "no Inverno). NOCs históricos ficam separados: a União Soviética (URS) "
        "não soma com a Rússia (RUS). " + EXPLICACAO_CONTAGEM
    )
    df = carregar(consultas.quadro_historico(season))
    _grafico_medalhas(df, "noc")
    mostrar_tabela(
        df,
        {
            "ranking_historico": formatar_ano,
            "edicoes_disputadas": formatar_inteiro,
            **FORMATOS_QUADRO,
        },
        COLUNAS_QUADRO,
    )


def ranking_de_atletas():
    st.subheader("Maiores medalhistas individuais")
    st.caption(
        "Soma Verão e Inverno. Aqui cada atleta premiado conta a sua medalha: "
        "cada jogador de um time campeão tem 1 ouro. Atletas que defenderam mais "
        "de um país aparecem com todos os NOCs (ex.: GDR | GER)."
    )
    limite = st.slider("Mostrar até a posição", 10, 100, 20, step=10)
    df = carregar(consultas.ranking_atletas(limite))
    mostrar_tabela(
        df,
        {
            "ranking": formatar_ano,
            "ouro": formatar_inteiro,
            "prata": formatar_inteiro,
            "bronze": formatar_inteiro,
            "total_medalhas": formatar_inteiro,
            "edicoes": formatar_inteiro,
        },
        {
            "ranking": "Posição",
            "name": "Atleta",
            "sex": "Sexo",
            "noc": "NOC",
            "ouro": "Ouro",
            "prata": "Prata",
            "bronze": "Bronze",
            "total_medalhas": "Total",
            "edicoes": "Edições",
        },
    )


def dominio_por_modalidade(season):
    st.subheader("Quem domina cada modalidade")
    st.caption(
        "Medalhas conquistadas por país na modalidade, somando todas as edições "
        "do período. A porcentagem é a fatia do país em todas as medalhas da "
        "modalidade; pelo arredondamento, a soma pode dar entre 99,95% e 100,08%."
    )
    lista = carregar(consultas.modalidades(season))["sport"].tolist()
    padrao = lista.index("Athletics") if "Athletics" in lista else 0
    sport = st.selectbox("Modalidade", lista, index=padrao, key="modalidade_dominio")
    df = carregar(consultas.dominio_modalidade(sport, season))
    st.bar_chart(
        df.head(10),
        x="noc",
        y="percentual_medalhas",
        horizontal=True,
        sort="-percentual_medalhas",
        x_label="% das medalhas da modalidade",
        y_label="",
    )
    mostrar_tabela(
        df,
        {
            "ranking_modalidade": formatar_ano,
            "percentual_medalhas": formatar_percentual,
            **{
                k: v for k, v in FORMATOS_QUADRO.items() if k != "registros_medalhistas"
            },
        },
        COLUNAS_QUADRO,
    )


def pagina():
    season = st.session_state["season"]
    nome_temporada = st.session_state["nome_temporada"]
    st.header(f"Medalhas — Jogos de {nome_temporada}")
    aba_edicao, aba_historico, aba_atletas, aba_modalidade = st.tabs(
        [
            "Por edição",
            "Quadro histórico",
            "Ranking de atletas",
            "Domínio por modalidade",
        ]
    )
    with aba_edicao:
        quadro_por_edicao(season)
    with aba_historico:
        quadro_historico(season, nome_temporada)
    with aba_atletas:
        ranking_de_atletas()
    with aba_modalidade:
        dominio_por_modalidade(season)

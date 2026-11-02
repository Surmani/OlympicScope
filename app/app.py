"""Dashboard OlympicScope — Etapa 5.

5.1: estrutura, Medalhas e Países; 5.2: Atletas e Os Jogos.

Como rodar: ``uv run streamlit run app/app.py`` (depois do pipeline) e abrir
http://localhost:8501.

Regras e motivos (spec, seção STREAMLIT)
----------------------------------------

- Lê só o schema ``marts`` e só faz ``SELECT ... WHERE`` (as consultas ficam
  em ``consultas.py``, testadas). Nenhuma soma, média ou contagem no app.
  Motivo: cada indicador tem um SQL versionado de onde saiu.
- Período dos dados sempre visível no topo de todas as páginas.
  Motivo: o dataset vai só até 2016 (Verão) e 2014 (Inverno); quem abre o
  painel pode supor que há edições mais recentes.
- Filtro de temporada no menu lateral, valendo para todas as páginas.
- Números no padrão brasileiro (``formatacao.py``); altura em metros e peso
  em quilogramas só na exibição.
- Se o banco não existir, avisa como gerar e para, sem criar nada.
  Motivo: um banco vazio na tela parece pipeline quebrado.
  Exceção (unidade 6.4): com o secret ``gerar_banco_se_faltar = true``,
  ligado só na hospedagem, o app gera o banco rodando o ``executar.py``
  (``preparo.py``), porque lá o disco é temporário e o banco não vem do Git.
- Gráficos nativos do Streamlit: os eixos saem no formato americano; tabelas
  e textos, no brasileiro (decisão registrada no README).

Critérios de aceite
-------------------

1. Sem banco: mensagem com o comando do pipeline, e nada é criado. (manual)
2. Com banco: as páginas Medalhas, Países, Atletas e Os Jogos abrem, com o
   período no topo e o filtro de temporada mudando os dados. (manual)
3. Consultas e formatação: ``tests/test_app_consultas.py`` e
   ``tests/test_app_formatacao.py``.
"""

import streamlit as st

import consultas
import preparo
from paginas import atletas, jogos, medalhas, paises

st.set_page_config(page_title="OlympicScope", page_icon="🏅", layout="wide")

TEMPORADAS = {"Verão": "Summer", "Inverno": "Winter"}

st.title("🏅 OlympicScope")
st.info(
    "**Período dos dados:** Jogos de Verão de 1896 (Athina) a 2016 (Rio de Janeiro) "
    "e Jogos de Inverno de 1924 (Chamonix) a 2014 (Sochi). Só os arquivos do "
    "Kaggle, coletados em 2018: edições posteriores **não estão** aqui. "
    "Art Competitions e os Jogos de 1906 ficam fora de todos os indicadores."
)

if not consultas.banco_existe() and preparo.geracao_ligada():
    with st.spinner(
        "Preparando os dados (cerca de 10 segundos, só na primeira visita)..."
    ):
        codigo, saida = preparo.gerar_banco()
    if codigo != 0:
        st.error("Não foi possível gerar o banco. Fim da saída do pipeline:")
        st.code(saida[-3000:])
        st.stop()

if not consultas.banco_existe():
    st.error(
        f"Banco não encontrado em `{consultas.CAMINHO_BANCO}`. Gere o banco antes:\n\n"
        "```\nuv run python -m pipeline.ingestao\nuv run python -m pipeline.refined\n"
        "uv run python -m pipeline.marts\n```"
    )
    st.stop()

with st.sidebar:
    nome_temporada = st.radio("Temporada", list(TEMPORADAS), horizontal=True)
    st.session_state["season"] = TEMPORADAS[nome_temporada]
    st.session_state["nome_temporada"] = nome_temporada
    st.caption("Fonte: 120 Years of Olympic History (Kaggle, CC0).")

navegacao = st.navigation(
    [
        st.Page(medalhas.pagina, title="Medalhas", icon="🥇", url_path="medalhas"),
        st.Page(paises.pagina, title="Países", icon="🌍", url_path="paises"),
        st.Page(atletas.pagina, title="Atletas", icon="🏃", url_path="atletas"),
        st.Page(jogos.pagina, title="Os Jogos", icon="🏟️", url_path="jogos"),
    ]
)
navegacao.run()

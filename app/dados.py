"""Cache das consultas do dashboard — unidade 5.1.

``carregar`` executa uma ``Consulta`` e guarda o resultado em ``st.cache_data``,
que é compartilhado entre todos os visitantes do app.

Motivo: o dashboard é só para consulta; com o cache, cada combinação de
filtros vai ao banco uma vez por hora, e o banco fica fechado no resto do
tempo (o pipeline pode rodar com o app aberto). Depois de rodar o pipeline,
os números novos aparecem quando o cache expira ou com "Clear cache" no menu
do Streamlit.
"""

import pandas as pd
import streamlit as st

import consultas


@st.cache_data(ttl=3600, show_spinner="Consultando o banco...")
def carregar(consulta: consultas.Consulta) -> pd.DataFrame:
    return consultas.executar(consulta)

"""Teste de fumaça das páginas do dashboard (unidade 6.2).

Abre as 4 páginas nas duas temporadas com o simulador do Streamlit (AppTest)
e falha se aparecer qualquer exceção. Nenhum teste abre data/olympics.duckdb:
os marts são criados num banco em tmp_path a partir da refined inventada dos
testes dos marts, e o app é apontado para ele.
"""

from pathlib import Path

import duckdb
import pytest
from streamlit.testing.v1 import AppTest
from test_marts_sql import criar_refined_inventada

from pipeline import executor_sql, marts

PASTA_APP = Path(__file__).resolve().parent.parent / "app"

PAGINAS = {
    "medalhas": "Medalhas — Jogos de",
    "paises": "Países — Jogos de",
    "atletas": "Atletas — Jogos de",
    "jogos": "Os Jogos —",
}


@pytest.fixture(scope="module")
def banco(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("paginas") / "teste.duckdb"
    conexao = duckdb.connect(str(caminho))
    criar_refined_inventada(conexao)
    executor_sql.executar(conexao, marts.PASTA_SQL, "marts")
    conexao.close()
    return caminho


def abrir_pagina(pasta_app, caminho_banco, nome_pagina, season, nome_temporada):
    """Roda dentro do AppTest: aponta o app para o banco temporário e abre a página."""
    import importlib
    import sys

    import streamlit as st

    if pasta_app not in sys.path:
        sys.path.insert(0, pasta_app)
    import consultas

    consultas.CAMINHO_BANCO = __import__("pathlib").Path(caminho_banco)
    st.cache_data.clear()
    st.session_state["season"] = season
    st.session_state["nome_temporada"] = nome_temporada
    importlib.import_module(f"paginas.{nome_pagina}").pagina()


@pytest.mark.parametrize("nome_pagina", PAGINAS)
@pytest.mark.parametrize(
    ("season", "nome_temporada"), [("Summer", "Verão"), ("Winter", "Inverno")]
)
def test_pagina_abre_sem_excecao(banco, nome_pagina, season, nome_temporada):
    at = AppTest.from_function(
        abrir_pagina,
        args=(str(PASTA_APP), str(banco), nome_pagina, season, nome_temporada),
        default_timeout=60,
    )
    at.run()

    assert [e.value for e in at.exception] == []
    assert at.header[0].value.startswith(PAGINAS[nome_pagina])
    assert nome_temporada in at.header[0].value
    assert len(at.dataframe) > 0


def test_filtro_sem_resultado_mostra_aviso_em_vez_de_grafico_vazio(banco):
    # Na refined inventada nenhuma delegação tem 10 atletas: com o corte padrão
    # (10), eficiência e perfil por país ficam vazios.
    at = AppTest.from_function(
        abrir_pagina,
        args=(str(PASTA_APP), str(banco), "paises", "Summer", "Verão"),
        default_timeout=60,
    )
    at.run()

    avisos = [i.value for i in at.info]
    assert sum("Nenhum dado com esses filtros" in a for a in avisos) == 2


@pytest.mark.parametrize("nome_pagina", ["paises", "atletas"])
def test_com_corte_em_1_graficos_e_tabelas_aparecem(banco, nome_pagina):
    at = AppTest.from_function(
        abrir_pagina,
        args=(str(PASTA_APP), str(banco), nome_pagina, "Summer", "Verão"),
        default_timeout=60,
    )
    at.run()
    for controle in at.slider:
        if "ínimo" in controle.label or "mínima" in controle.label:
            controle.set_value(1)
    at.run()

    assert [e.value for e in at.exception] == []
    assert not any("Nenhum dado" in i.value for i in at.info)


# --- app.py: topo do app, banco inexistente e menu --------------------------------


@pytest.fixture
def consultas_do_app(monkeypatch):
    """O módulo consultas como o app o importa (app/ no caminho do Python)."""
    import importlib
    import sys

    import streamlit as st

    monkeypatch.syspath_prepend(str(PASTA_APP))
    modulo = importlib.import_module("consultas")
    st.cache_data.clear()
    yield modulo
    st.cache_data.clear()
    sys.modules.pop("consultas", None)


def test_app_mostra_o_periodo_e_abre_a_primeira_pagina(
    banco, consultas_do_app, monkeypatch
):
    monkeypatch.setattr(consultas_do_app, "CAMINHO_BANCO", banco)
    at = AppTest.from_file(str(PASTA_APP / "app.py"), default_timeout=60)
    at.run()

    assert [e.value for e in at.exception] == []
    aviso = at.info[0].value
    assert "1896" in aviso and "2016" in aviso and "1924" in aviso and "2014" in aviso
    assert at.sidebar.radio[0].options == ["Verão", "Inverno"]
    assert at.header[0].value == "Medalhas — Jogos de Verão"


def test_app_sem_banco_avisa_e_nao_cria_nada(tmp_path, consultas_do_app, monkeypatch):
    inexistente = tmp_path / "data" / "olympics.duckdb"
    monkeypatch.setattr(consultas_do_app, "CAMINHO_BANCO", inexistente)
    at = AppTest.from_file(str(PASTA_APP / "app.py"), default_timeout=60)
    at.run()

    assert [e.value for e in at.exception] == []
    assert "uv run python -m pipeline.ingestao" in at.error[0].value
    assert len(at.header) == 0  # nenhuma página foi aberta
    assert not inexistente.exists()
    assert not inexistente.parent.exists()


# --- 6.4: gerar o banco na hospedagem ------------------------------------------------


@pytest.fixture
def preparo_do_app(consultas_do_app):
    """O módulo preparo como o app o importa, com o cache de recurso limpo."""
    import importlib
    import sys

    import streamlit as st

    modulo = importlib.import_module("preparo")
    st.cache_resource.clear()
    yield modulo
    st.cache_resource.clear()
    sys.modules.pop("preparo", None)


def test_app_sem_banco_com_secret_gera_o_banco_e_abre(
    tmp_path, banco, consultas_do_app, preparo_do_app, monkeypatch
):
    import shutil
    import subprocess

    destino = tmp_path / "data" / "olympics.duckdb"
    monkeypatch.setattr(consultas_do_app, "CAMINHO_BANCO", destino)
    chamadas = []

    def pipeline_falso():
        # No lugar do executar.py real: copia o banco de teste para o destino.
        chamadas.append(1)
        destino.parent.mkdir(parents=True)
        shutil.copy(banco, destino)
        return subprocess.CompletedProcess([], 0, "verificações: 12 de 12 ok\n", "")

    monkeypatch.setattr(preparo_do_app, "executar_pipeline", pipeline_falso)
    at = AppTest.from_file(str(PASTA_APP / "app.py"), default_timeout=60)
    at.secrets["gerar_banco_se_faltar"] = True
    at.run()

    assert [e.value for e in at.exception] == []
    assert chamadas == [1]
    assert destino.exists()
    assert at.header[0].value == "Medalhas — Jogos de Verão"

    at.run()  # segunda visita no mesmo servidor: não gera de novo
    assert chamadas == [1]


def test_app_geracao_que_falha_mostra_a_saida_e_para(
    tmp_path, consultas_do_app, preparo_do_app, monkeypatch
):
    import subprocess

    monkeypatch.setattr(
        consultas_do_app, "CAMINHO_BANCO", tmp_path / "data" / "olympics.duckdb"
    )
    monkeypatch.setattr(
        preparo_do_app,
        "executar_pipeline",
        lambda: subprocess.CompletedProcess(
            [], 1, "", "Parou na etapa 2/3: Refined.\n"
        ),
    )
    at = AppTest.from_file(str(PASTA_APP / "app.py"), default_timeout=60)
    at.secrets["gerar_banco_se_faltar"] = True
    at.run()

    assert "Não foi possível gerar o banco" in at.error[0].value
    assert "Parou na etapa 2/3" in at.code[0].value
    assert len(at.header) == 0


def test_sem_secret_a_geracao_fica_desligada(preparo_do_app):
    assert preparo_do_app.geracao_ligada() is False


def test_requirements_txt_bate_com_o_uv_lock():
    import shutil
    import subprocess

    if shutil.which("uv") is None:
        pytest.skip("uv não está no PATH")
    raiz = PASTA_APP.parent
    gerado = subprocess.run(
        [
            "uv", "export", "--no-dev", "--no-hashes", "--no-emit-project",
            "--frozen", "--format", "requirements-txt",
        ],
        cwd=raiz, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip

    def pacotes(texto):
        return [linha for linha in texto.splitlines() if not linha.startswith("#")]

    atual = (raiz / "requirements.txt").read_text(encoding="utf-8")
    assert pacotes(atual) == pacotes(gerado), (
        "requirements.txt desatualizado: rode o comando do topo do arquivo"
    )

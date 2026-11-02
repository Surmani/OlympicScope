"""Testes de executar.py.

Nenhum teste abre data/olympics.duckdb nem lê raw/: os CSVs são inventados em
tmp_path e o banco é temporário. Os SQL de refined e marts são os reais.
"""

import duckdb
import pytest

import executar
from pipeline import db

CABECALHO = (
    '"ID","Name","Sex","Age","Height","Weight","Team","NOC","Games","Year",'
    '"Season","City","Sport","Event","Medal"\n'
)
ATHLETE_EVENTS = CABECALHO + (
    '"1","Ana","F","24","170","60","Brazil","BRA","2016 Summer","2016","Summer",'
    '"Rio de Janeiro","Swimming","Swimming Women\'s 100 metres","Gold"\n'
    '"2","Bo","M","NA","NA","NA","Argentina","ARG","2016 Summer","2016","Summer",'
    '"Rio de Janeiro","Swimming","Swimming Women\'s 100 metres","NA"\n'
    '"3","Cy","M","30","180","80.5","Brazil","BRA","2014 Winter","2014","Winter",'
    '"Sochi","Alpine Skiing","Alpine Skiing Men\'s Downhill","Silver"\n'
)
NOC_REGIONS = "NOC,region,notes\nARG,Argentina,\nBRA,Brazil,\n"


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    pasta_raw = tmp_path / "raw"
    pasta_raw.mkdir()
    (pasta_raw / "athlete_events.csv").write_text(ATHLETE_EVENTS, encoding="utf-8")
    (pasta_raw / "noc_regions.csv").write_text(NOC_REGIONS, encoding="utf-8")
    banco = tmp_path / "data" / "teste.duckdb"
    monkeypatch.setattr(db, "PASTA_RAW", pasta_raw)
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)
    return pasta_raw, banco


def tabelas(banco):
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return {
            f"{schema}.{tabela}"
            for schema, tabela in con.execute(
                "SELECT table_schema, table_name FROM information_schema.tables"
            ).fetchall()
        }
    finally:
        con.close()


def test_reconstroi_as_tres_camadas(ambiente, capsys):
    _, banco = ambiente
    executar.main()

    saida = capsys.readouterr().out
    assert "== 1/3 Ingestão" in saida
    assert "== 2/3 Refined" in saida
    assert "== 3/3 Marts" in saida
    assert "verificações: 12 de 12 ok" in saida
    assert "Pronto: banco recriado do zero" in saida

    criadas = tabelas(banco)
    assert {"raw.athlete_events", "raw.noc_regions"} <= criadas
    assert "refined.athlete_results" in criadas
    assert len({t for t in criadas if t.startswith("marts.")}) == 15


def test_tabela_antiga_some(ambiente):
    _, banco = ambiente
    banco.parent.mkdir(parents=True)
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.mart_renomeado AS SELECT 1 AS x")
    con.close()

    executar.main()

    assert "marts.mart_renomeado" not in tabelas(banco)


def test_arquivo_faltando_nao_apaga_o_banco(ambiente):
    pasta_raw, banco = ambiente
    banco.parent.mkdir(parents=True)
    con = duckdb.connect(str(banco))
    con.execute("CREATE TABLE guardada AS SELECT 1 AS x")
    con.close()
    (pasta_raw / "noc_regions.csv").unlink()

    with pytest.raises(SystemExit) as saida_programa:
        executar.main()

    assert saida_programa.value.code == 1
    assert "main.guardada" in tabelas(banco)


def test_banco_travado_avisa_e_nao_roda_nada(ambiente, monkeypatch, capsys):
    _, banco = ambiente

    def travado(self, missing_ok=False):
        raise PermissionError("arquivo em uso")

    monkeypatch.setattr(type(banco), "unlink", travado)

    with pytest.raises(SystemExit) as saida_programa:
        executar.main()

    assert saida_programa.value.code == 1
    saida = capsys.readouterr()
    assert "ui.py" in saida.err
    assert "== 1/3" not in saida.out


def test_etapa_que_falha_interrompe_as_seguintes(ambiente, monkeypatch, capsys):
    rodou = []

    def falha():
        raise SystemExit(1)

    monkeypatch.setattr(
        executar,
        "ETAPAS",
        (
            ("primeira", lambda: rodou.append("primeira")),
            ("segunda", falha),
            ("terceira", lambda: rodou.append("terceira")),
        ),
    )

    with pytest.raises(SystemExit) as saida_programa:
        executar.main()

    assert saida_programa.value.code == 1
    assert rodou == ["primeira"]
    assert "Parou na etapa 2/3: segunda." in capsys.readouterr().err

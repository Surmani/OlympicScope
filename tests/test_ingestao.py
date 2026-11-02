"""Testes de pipeline/ingestao.py.

Nenhum teste lê raw/ nem abre data/olympics.duckdb: as pastas de origem e o
banco são inventados em tmp_path.
"""

import duckdb
import pytest

from pipeline import db, ingestao

ATHLETE_EVENTS_INVENTADO = (
    '"ID","Name","Sex","Age","Medal"\n'
    '"1","Ana Souza","F","24","Gold"\n'
    '"2","João Silva","M","NA","NA"\n'
    '"3","Maria, a Grande","F","31","NA"\n'
)

NOC_REGIONS_INVENTADO = "NOC,region,notes\nBRA,Brazil,\nURS,Russia,\n"


def criar_arquivos(pasta, nomes):
    for nome in nomes:
        (pasta / nome).write_text("inventado\n", encoding="utf-8")


def test_todos_presentes_nao_falta_nada(tmp_path, capsys):
    criar_arquivos(tmp_path, ingestao.ARQUIVOS)

    assert ingestao.arquivos_faltando(tmp_path) == []
    ingestao.validar_arquivos(tmp_path)

    saida = capsys.readouterr()
    assert saida.out == ""
    assert saida.err == ""


def test_falta_um_arquivo(tmp_path):
    criar_arquivos(tmp_path, ["athlete_events.csv"])

    assert ingestao.arquivos_faltando(tmp_path) == ["noc_regions.csv"]


def test_faltam_todos_na_ordem_de_arquivos(tmp_path):
    assert ingestao.arquivos_faltando(tmp_path) == list(ingestao.ARQUIVOS)


def test_pasta_com_nome_de_arquivo_conta_como_faltando(tmp_path):
    criar_arquivos(tmp_path, ["noc_regions.csv"])
    (tmp_path / "athlete_events.csv").mkdir()

    assert ingestao.arquivos_faltando(tmp_path) == ["athlete_events.csv"]


def test_validar_encerra_com_codigo_1_e_lista_em_stderr(tmp_path, capsys):
    with pytest.raises(SystemExit) as saida_programa:
        ingestao.validar_arquivos(tmp_path)

    assert saida_programa.value.code == 1

    saida = capsys.readouterr()
    assert saida.out == ""
    assert str(tmp_path) in saida.err
    for nome in ingestao.ARQUIVOS:
        assert nome in saida.err


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Pasta raw inventada e banco temporário, no lugar dos caminhos reais."""
    pasta_raw = tmp_path / "raw"
    pasta_raw.mkdir()
    (pasta_raw / "athlete_events.csv").write_text(
        ATHLETE_EVENTS_INVENTADO, encoding="utf-8"
    )
    (pasta_raw / "noc_regions.csv").write_text(NOC_REGIONS_INVENTADO, encoding="utf-8")
    banco = tmp_path / "data" / "teste.duckdb"
    monkeypatch.setattr(db, "PASTA_RAW", pasta_raw)
    monkeypatch.setattr(db, "CAMINHO_BANCO", banco)
    return pasta_raw, banco


def consultar(banco, sql):
    con = duckdb.connect(str(banco), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_na_continua_texto(ambiente):
    _, banco = ambiente
    ingestao.ingerir()

    linhas = consultar(banco, 'SELECT "Age", "Medal" FROM raw.athlete_events')
    assert ("NA", "NA") in linhas
    nulos = consultar(
        banco,
        'SELECT COUNT(*) FROM raw.athlete_events WHERE "Age" IS NULL OR "Medal" IS '
        "NULL",
    )
    assert nulos == [(0,)]


def test_todas_as_colunas_sao_varchar_com_nomes_da_origem(ambiente):
    _, banco = ambiente
    ingestao.ingerir()

    colunas = consultar(
        banco,
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'raw' ORDER BY table_name, ordinal_position",
    )
    assert colunas == [
        ("athlete_events", "ID", "VARCHAR"),
        ("athlete_events", "Name", "VARCHAR"),
        ("athlete_events", "Sex", "VARCHAR"),
        ("athlete_events", "Age", "VARCHAR"),
        ("athlete_events", "Medal", "VARCHAR"),
        ("noc_regions", "NOC", "VARCHAR"),
        ("noc_regions", "region", "VARCHAR"),
        ("noc_regions", "notes", "VARCHAR"),
    ]


def test_valores_chegam_sem_alteracao(ambiente):
    _, banco = ambiente
    ingestao.ingerir()

    nomes = consultar(banco, 'SELECT "Name" FROM raw.athlete_events ORDER BY "ID"')
    assert nomes == [("Ana Souza",), ("João Silva",), ("Maria, a Grande",)]


def test_ingerir_devolve_contagens_do_banco(ambiente):
    assert ingestao.ingerir() == {"raw.athlete_events": 3, "raw.noc_regions": 2}


def test_rodar_duas_vezes_imprime_igual_e_nao_duplica(ambiente, capsys):
    _, banco = ambiente
    ingestao.main()
    primeira = capsys.readouterr().out
    ingestao.main()
    segunda = capsys.readouterr().out

    assert primeira == segunda
    assert primeira == (
        "raw.athlete_events: 3 linhas\nraw.noc_regions: 2 linhas\nTotal: 5 linhas\n"
    )
    assert consultar(banco, "SELECT COUNT(*) FROM raw.athlete_events") == [(3,)]


def test_arquivo_faltando_encerra_sem_criar_banco(ambiente):
    pasta_raw, banco = ambiente
    (pasta_raw / "noc_regions.csv").unlink()

    with pytest.raises(SystemExit) as saida_programa:
        ingestao.main()

    assert saida_programa.value.code == 1
    assert not banco.exists()
    assert not banco.parent.exists()


@pytest.mark.parametrize(
    ("numero", "esperado"),
    [(0, "0"), (230, "230"), (1000, "1.000"), (271116, "271.116")],
)
def test_formatar_milhar(numero, esperado):
    assert ingestao.formatar_milhar(numero) == esperado

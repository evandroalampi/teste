import pytest

from clima_varejo.agentes.clima.fontes import inmet
from clima_varejo.agentes.clima.ingestao import normalizar_inmet
from clima_varejo.dominio.clima import COLUNAS_CLIMA_HORA

REGRAS = {
    "interpolar_temperatura_max_horas": 3,
    "faixas": {"temperatura_c": [-10, 45], "umidade_pct": [0, 100]},
}


def _normalizado(csv_bytes):
    meta, dados = inmet.ler_csv_estacao(csv_bytes)
    return normalizar_inmet(meta, dados, "pacote_anual_2025", REGRAS)


def test_layout_do_contrato(csv_inmet):
    df = _normalizado(csv_inmet())
    assert list(df.columns) == COLUNAS_CLIMA_HORA
    assert (df["fonte"] == "INMET").all()


def test_hora_local_utc_menos_3(csv_inmet):
    df = _normalizado(csv_inmet())
    diff = df["data_hora_utc"].dt.tz_localize(None) - df["data_hora_local"]
    assert (diff.dt.total_seconds() == 3 * 3600).all()


def test_radiacao_convertida_e_noite_zerada(csv_inmet):
    df = _normalizado(csv_inmet())
    meio_dia = df[df["data_hora_utc"].dt.hour == 15]["radiacao_w_m2"].iat[0]
    assert meio_dia == pytest.approx(2600 * 1.0 / 3.6, rel=0.05)  # kJ/m² ÷ 3,6
    madrugada = df[df["data_hora_utc"].dt.hour == 4]
    assert (madrugada["radiacao_w_m2"] == 0).all()
    assert madrugada["flag_qualidade"].str.contains("radiacao_noturna_zero").all()


def test_interpola_ate_3h_e_marca_lacunas_longas(csv_inmet):
    df = _normalizado(csv_inmet(lacunas_temp={5: 3, 20: 6}))
    curta = df.iloc[5:8]
    assert curta["temperatura_c"].notna().all()
    assert curta["flag_qualidade"].str.contains("interpolado").all()
    longa = df.iloc[20:26]
    assert longa["temperatura_c"].isna().all()
    assert longa["flag_qualidade"].str.contains("lacuna").all()


def test_chuva_nunca_interpolada(csv_inmet):
    df = _normalizado(csv_inmet(chuva_vazia={10}))
    assert df["precipitacao_mm"].isna().iat[10]

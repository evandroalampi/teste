import pandas as pd
import pytest

from clima_varejo.agentes.clima.fontes import inmet


def test_metadados_e_colunas(csv_inmet):
    meta, df = inmet.ler_csv_estacao(csv_inmet())
    assert meta.codigo_wmo == "A999"
    assert meta.latitude == pytest.approx(-26.90)
    assert meta.data_fundacao.isoformat() == "2017-12-20"
    # Coluna fantasma descartada; todas as 19 colunas padronizadas (data+hora viram data_hora_utc).
    assert "radiacao_kj_m2" in df and "temperatura_c" in df and "vento_dir" in df
    assert len(df.columns) == 1 + 17
    assert not any(c.startswith("Unnamed") for c in df.columns)


def test_hora_em_utc_e_decimal_virgula(csv_inmet):
    _, df = inmet.ler_csv_estacao(csv_inmet())
    assert df["data_hora_utc"].iat[0] == pd.Timestamp("2025-01-01 00:00", tz="UTC")
    assert df.loc[df["data_hora_utc"].dt.hour == 18, "precipitacao_mm"].iat[0] == pytest.approx(0.8)


def test_nulos_vazio_e_9999():
    assert inmet._numero_br("") is None
    assert inmet._numero_br("-9999") is None
    assert inmet._numero_br(",8") == pytest.approx(0.8)


@pytest.mark.parametrize(
    "original,esperado",
    [
        ("PRECIPITAÇÃO TOTAL, HORÁRIO (mm)", "precipitacao_mm"),
        ("PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)", "pressao_max_mb"),
        ("TEMPERATURA DO PONTO DE ORVALHO (°C)", "orvalho_c"),
        ("TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C)", "orvalho_min_c"),
        ("UMIDADE RELATIVA DO AR, HORARIA (%)", "umidade_pct"),
        ("DATA (YYYY-MM-DD)", "data"),       # layout de anos anteriores
        ("HORA (UTC)", "hora_utc"),
    ],
)
def test_padronizacao_por_texto(original, esperado):
    assert inmet.padronizar_coluna(original) == esperado


def test_formato_antigo_de_data_e_hora():
    s = inmet._montar_data_hora_utc(pd.Series(["2019-03-01"]), pd.Series(["13:00"]))
    assert s.iat[0] == pd.Timestamp("2019-03-01 13:00", tz="UTC")


def test_coluna_desconhecida_falha(csv_inmet):
    texto = csv_inmet().decode("latin-1").replace("VENTO, VELOCIDADE", "COLUNA NOVA")
    with pytest.raises(ValueError, match="sem padrão"):
        inmet.ler_csv_estacao(texto)

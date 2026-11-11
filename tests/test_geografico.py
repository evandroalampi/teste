import pandas as pd
import pytest

from clima_varejo.agentes.geografico.mapeamento import haversine_km, mapear


def test_haversine():
    # Blumenau -> Indaial, ~13-17 km
    assert 10 < haversine_km(-26.919, -49.066, -26.897, -49.232) < 20
    assert haversine_km(0, 0, 0, 0) == pytest.approx(0)


def _lojas():
    return pd.DataFrame([
        {"idvarejista": "redetop-indaial-sc", "idloja": 1, "latitude": -26.90, "longitude": -49.23},
        {"idvarejista": "preceiro-indaial-sc", "idloja": 1, "latitude": -26.60, "longitude": -48.70},
    ])


def _pontos():
    return pd.DataFrame([
        {"id_ponto": "A817", "fonte": "INMET", "latitude": -26.91, "longitude": -49.27},
        {"id_ponto": "PLUV1", "fonte": "CEMADEN", "latitude": -26.61, "longitude": -48.71},
        {"id_ponto": "ERA_1", "fonte": "ERA5_LAND", "latitude": -26.60, "longitude": -48.70},
    ])


def test_id_repetido_entre_bandeiras_nao_colide():
    m = mapear(_lojas(), _pontos(), ["temperatura_c"])
    assert len(m) == 2
    assert set(m["idvarejista"]) == {"redetop-indaial-sc", "preceiro-indaial-sc"}


def test_estacao_proxima_vence_e_grade_cobre_loja_distante():
    m = mapear(_lojas(), _pontos(), ["temperatura_c"]).set_index("idvarejista")
    assert m.loc["redetop-indaial-sc", "id_ponto"] == "A817"
    assert m.loc["preceiro-indaial-sc", "id_ponto"] == "ERA_1"


def test_chuva_prefere_pluviometro_mais_proximo():
    m = mapear(_lojas(), _pontos(), ["precipitacao_mm"]).set_index("idvarejista")
    assert m.loc["preceiro-indaial-sc", "id_ponto"] == "PLUV1"
    assert m.loc["redetop-indaial-sc", "id_ponto"] == "A817"

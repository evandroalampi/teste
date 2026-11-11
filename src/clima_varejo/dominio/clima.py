"""Modelo da tabela de clima unificada (seção 14 do documento de escopo)."""

from __future__ import annotations

from enum import StrEnum

FUSO_LOCAL = "America/Sao_Paulo"  # UTC-3 fixo no período (sem horário de verão desde 2019)


class Fonte(StrEnum):
    INMET = "INMET"
    EPAGRI = "EPAGRI"
    CEMADEN = "CEMADEN"
    ERA5_LAND = "ERA5_LAND"
    OPEN_METEO = "OPEN_METEO"
    GPM_IMERG = "GPM_IMERG"
    NASA_POWER = "NASA_POWER"
    NOAA_ISD = "NOAA_ISD"


class Flag(StrEnum):
    """Marcas de qualidade. Um registro pode ter várias, separadas por '|'."""

    LACUNA = "lacuna"
    INTERPOLADO = "interpolado"
    FORA_FAIXA = "fora_faixa"
    RADIACAO_NOTURNA_ZERO = "radiacao_noturna_zero"


# Colunas da contrato.clima_hora, na ordem do banco.
COLUNAS_CLIMA_HORA = [
    "id_ponto", "data_hora_utc", "data_hora_local", "fuso_horario",
    "latitude", "longitude", "elevacao_m",
    "temperatura_c", "temp_max_c", "temp_min_c", "sensacao_termica_c",
    "precipitacao_mm", "radiacao_w_m2", "umidade_pct", "nebulosidade_pct",
    "vento_ms", "rajada_ms", "vento_dir", "pressao_mb",
    "fonte", "versao_fonte", "flag_qualidade", "data_coleta",
]

CHAVE_CLIMA_HORA = ["id_ponto", "data_hora_utc", "fonte"]

VARIAVEIS_MEDIDAS = [
    "temperatura_c", "temp_max_c", "temp_min_c", "sensacao_termica_c",
    "precipitacao_mm", "radiacao_w_m2", "umidade_pct", "nebulosidade_pct",
    "vento_ms", "rajada_ms", "vento_dir", "pressao_mb",
]


def kj_m2_para_w_m2(valor_kj_m2):
    """Radiação acumulada na hora (kJ/m²) para média da hora (W/m²): ÷ 3,6."""
    return valor_kj_m2 / 3.6

"""Regras de qualidade do agente de clima (seções 12 e 14).

- Radiação vazia com o sol abaixo do horizonte vira 0; falha diurna fica nula.
- Temperatura: interpolar lacunas de até 3 horas. Chuva nunca é interpolada.
- Valores fora de faixa e lacunas são marcados em flag_qualidade, nunca descartados.
- Completude: 8.760 horas por ano (8.784 em ano bissexto).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ...dominio.clima import Flag


def elevacao_solar_graus(data_hora_utc: pd.Series, latitude: float, longitude: float) -> np.ndarray:
    """Elevação aproximada do sol (graus), pela equação do tempo da NOAA.

    Usa o meio da hora anterior, pois a radiação do INMET é acumulada na hora que termina em H.
    """
    t = pd.DatetimeIndex(data_hora_utc) - pd.Timedelta(minutes=30)
    dia_ano = t.dayofyear.to_numpy()
    hora = t.hour.to_numpy() + t.minute.to_numpy() / 60
    gama = 2 * np.pi / 365 * (dia_ano - 1 + (hora - 12) / 24)
    eq_tempo = 229.18 * (
        0.000075 + 0.001868 * np.cos(gama) - 0.032077 * np.sin(gama)
        - 0.014615 * np.cos(2 * gama) - 0.040849 * np.sin(2 * gama)
    )
    declinacao = (
        0.006918 - 0.399912 * np.cos(gama) + 0.070257 * np.sin(gama)
        - 0.006758 * np.cos(2 * gama) + 0.000907 * np.sin(2 * gama)
        - 0.002697 * np.cos(3 * gama) + 0.00148 * np.sin(3 * gama)
    )
    tempo_solar_min = hora * 60 + eq_tempo + 4 * longitude
    angulo_horario = np.radians(tempo_solar_min / 4 - 180)
    lat = np.radians(latitude)
    cos_zenite = np.sin(lat) * np.sin(declinacao) + np.cos(lat) * np.cos(declinacao) * np.cos(angulo_horario)
    return 90 - np.degrees(np.arccos(np.clip(cos_zenite, -1, 1)))


def _adicionar_flag(flags: pd.Series, mascara, flag: Flag) -> pd.Series:
    mascara = pd.Series(mascara, index=flags.index).fillna(False).astype(bool)
    novo = flags.where(~mascara, flags.fillna("").str.cat([flag.value] * len(flags), sep="|").str.strip("|"))
    return novo


def zerar_radiacao_noturna(
    df: pd.DataFrame, latitude: float, longitude: float, coluna: str = "radiacao_w_m2", limite_graus: float = -0.833
) -> pd.DataFrame:
    df = df.copy()
    noite = elevacao_solar_graus(df["data_hora_utc"], latitude, longitude) < limite_graus
    vazia_a_noite = noite & df[coluna].isna().to_numpy()
    df.loc[vazia_a_noite, coluna] = 0.0
    df["flag_qualidade"] = _adicionar_flag(df["flag_qualidade"], vazia_a_noite, Flag.RADIACAO_NOTURNA_ZERO)
    return df


def interpolar_lacunas_curtas(df: pd.DataFrame, coluna: str, max_horas: int) -> pd.DataFrame:
    """Interpola linearmente só as lacunas com até `max_horas` horas consecutivas."""
    df = df.copy()
    vazio = df[coluna].isna()
    grupo = (vazio != vazio.shift()).cumsum()
    tamanho = vazio.groupby(grupo).transform("sum")
    interior = df[coluna].ffill().notna() & df[coluna].bfill().notna()
    curta = vazio & (tamanho <= max_horas) & interior
    interpolada = df[coluna].interpolate(method="linear", limit_area="inside")
    df.loc[curta, coluna] = interpolada[curta]
    df["flag_qualidade"] = _adicionar_flag(df["flag_qualidade"], curta, Flag.INTERPOLADO)
    df["flag_qualidade"] = _adicionar_flag(df["flag_qualidade"], vazio & ~curta, Flag.LACUNA)
    return df


def marcar_fora_de_faixa(df: pd.DataFrame, faixas: dict[str, list[float]]) -> pd.DataFrame:
    df = df.copy()
    for coluna, (minimo, maximo) in faixas.items():
        if coluna in df:
            fora = df[coluna].notna() & ~df[coluna].between(minimo, maximo)
            df["flag_qualidade"] = _adicionar_flag(df["flag_qualidade"], fora, Flag.FORA_FAIXA)
    return df


def horas_esperadas(ano: int) -> int:
    return 8784 if pd.Timestamp(year=ano, month=12, day=31).dayofyear == 366 else 8760


def checar_completude(df: pd.DataFrame, ano: int) -> dict:
    do_ano = df[df["data_hora_utc"].dt.year == ano]
    esperado = horas_esperadas(ano)
    return {"ano": ano, "linhas": len(do_ano), "esperado": esperado, "completo": len(do_ano) == esperado}

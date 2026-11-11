"""Mapeamento loja x ponto climático (seções 10, 15 e 16).

Para cada loja e variável, escolhe o ponto mais próximo seguindo a hierarquia de fontes:
observação local (INMET, Epagri) -> chuva adensada (Cemaden, só precipitação)
-> grade (ERA5-Land) quando nenhuma estação está a até `raio_max_km`.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

RAIO_TERRA_KM = 6371.0088

# Variáveis que cada tipo de fonte mede.
VARIAVEIS_POR_FONTE = {
    "INMET": {"temperatura_c", "precipitacao_mm", "radiacao_w_m2", "umidade_pct"},
    "EPAGRI": {"temperatura_c", "precipitacao_mm", "radiacao_w_m2", "umidade_pct"},
    "CEMADEN": {"precipitacao_mm"},
    "ERA5_LAND": {"temperatura_c", "precipitacao_mm", "radiacao_w_m2", "umidade_pct"},
}
PRIORIDADE = ["INMET", "EPAGRI", "CEMADEN", "ERA5_LAND"]


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def distancias(lojas: pd.DataFrame, pontos: pd.DataFrame) -> pd.DataFrame:
    """Produto cartesiano loja x ponto com a distância em km."""
    cruz = lojas[["idvarejista", "idloja", "latitude", "longitude"]].merge(
        pontos[["id_ponto", "fonte", "latitude", "longitude"]], how="cross", suffixes=("_loja", "_ponto")
    )
    cruz["distancia_km"] = haversine_km(
        cruz["latitude_loja"], cruz["longitude_loja"], cruz["latitude_ponto"], cruz["longitude_ponto"]
    )
    return cruz


def mapear(
    lojas: pd.DataFrame,
    pontos: pd.DataFrame,
    variaveis: list[str],
    raio_max_km: float = 15.0,
    data_inicio: date | None = None,
) -> pd.DataFrame:
    """Escolhe um ponto por loja e variável.

    Regra: o ponto observado mais próximo vence se estiver a até `raio_max_km`; para chuva,
    um pluviômetro do Cemaden mais perto que a estação escolhida vence. Sem ponto observado
    no raio, usa a grade (ERA5-Land); sem grade carregada, fica a estação mais próxima.
    O raio padrão de 15 km é uma proposta: só 5 lojas ficam a até 15 km de uma estação INMET.
    """
    lojas = lojas.dropna(subset=["latitude", "longitude"])
    cruz = distancias(lojas, pontos)
    data_inicio = data_inicio or date.today()
    escolhas = []
    for (idvarejista, idloja), grupo in cruz.groupby(["idvarejista", "idloja"]):
        for variavel in variaveis:
            candidatos = grupo[grupo["fonte"].map(lambda f: variavel in VARIAVEIS_POR_FONTE.get(f, set()))]
            if candidatos.empty:
                continue
            observados = candidatos[candidatos["fonte"].isin(["INMET", "EPAGRI"])].nsmallest(1, "distancia_km")
            escolha = observados
            if variavel == "precipitacao_mm":
                pluv = candidatos[candidatos["fonte"] == "CEMADEN"].nsmallest(1, "distancia_km")
                if not pluv.empty and (escolha.empty or pluv["distancia_km"].iat[0] < escolha["distancia_km"].iat[0]):
                    escolha = pluv
            if escolha.empty or escolha["distancia_km"].iat[0] > raio_max_km:
                grade = candidatos[candidatos["fonte"] == "ERA5_LAND"].nsmallest(1, "distancia_km")
                if not grade.empty:
                    escolha = grade
            if escolha.empty:
                escolha = candidatos.nsmallest(1, "distancia_km")
            linha = escolha.iloc[0]
            escolhas.append({
                "idvarejista": idvarejista, "idloja": int(idloja), "variavel": variavel,
                "id_ponto": linha["id_ponto"], "fonte": linha["fonte"],
                "distancia_km": round(float(linha["distancia_km"]), 2), "data_inicio": data_inicio,
            })
    return pd.DataFrame(escolhas)

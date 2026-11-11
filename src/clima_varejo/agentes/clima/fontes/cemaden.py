"""Cemaden: pluviômetros automáticos (só chuva), densos em áreas de risco. Seção 15.

Regras já conhecidas:
- Registro horário sem chuva e a cada 10 minutos com chuva -> reagregar para a hora que termina em H.
- Há estações com meses sem dados: exige controle de qualidade (flag, não descarte).
Pendências: mapear pluviômetros perto das lojas (Mapa Interativo) e confirmar a licença.
"""

from __future__ import annotations

import pandas as pd


def agregar_por_hora(registros: pd.DataFrame) -> pd.DataFrame:
    """Soma a chuva dos registros (data_hora_utc, precipitacao_mm) na hora que termina em H."""
    df = registros.copy()
    df["data_hora_utc"] = df["data_hora_utc"].dt.ceil("h")
    return df.groupby("data_hora_utc", as_index=False)["precipitacao_mm"].sum(min_count=1)


def ler_estacao(*_args, **_kwargs) -> pd.DataFrame:
    raise NotImplementedError("Aguardando mapeamento dos pluviômetros e formato de download.")

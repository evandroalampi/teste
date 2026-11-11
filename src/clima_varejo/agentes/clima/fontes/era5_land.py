"""ERA5-Land via Copernicus CDS: grade de ~11 km para preencher lacunas. Seções 13 e 15.

- Licença CC BY: uso comercial gratuito com atribuição (substitui a Open-Meteo na produção).
- Entrega NetCDF/GRIB por área: extrair a célula de cada loja.
- Fixar o modelo e gravar em versao_fonte (ex.: 'ERA5-Land').
- Precipitação e radiação são acumuladas: converter para o acumulado/média da hora que termina em H.
Pendência: conta no CDS, aceite da licença e token em CDSAPI_KEY.
"""

from __future__ import annotations

import pandas as pd

VARIAVEIS_CDS = {
    "2m_temperature": "temperatura_c",
    "total_precipitation": "precipitacao_mm",
    "surface_solar_radiation_downwards": "radiacao_w_m2",
    "2m_dewpoint_temperature": "orvalho_c",
}


def baixar_area(*_args, **_kwargs):
    raise NotImplementedError("Aguardando conta no Copernicus CDS (CDSAPI_KEY).")


def extrair_pontos(*_args, **_kwargs) -> pd.DataFrame:
    raise NotImplementedError("Implementar após o primeiro download de teste.")

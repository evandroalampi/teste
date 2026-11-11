"""Fixtures: CSV sintético no layout do pacote anual 2025 do INMET (seção 12)."""

from __future__ import annotations

import math

import pytest

COLUNAS_2025 = [
    "Data", "Hora UTC", "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)",
    "PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)", "PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB)",
    "RADIACAO GLOBAL (Kj/m²)", "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)",
    "TEMPERATURA DO PONTO DE ORVALHO (°C)", "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)",
    "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)", "TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C)",
    "TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C)", "UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)",
    "UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)", "UMIDADE RELATIVA DO AR, HORARIA (%)",
    "VENTO, DIREÇÃO HORARIA (gr) (° (gr))", "VENTO, RAJADA MAXIMA (m/s)", "VENTO, VELOCIDADE HORARIA (m/s)",
]

METADADOS = """REGIAO:;S
UF:;SC
ESTACAO:;TESTE
CODIGO (WMO):;A999
LATITUDE:;-26,90
LONGITUDE:;-49,23
ALTITUDE:;86
DATA DE FUNDACAO:;20/12/17
"""


def _br(v):
    return "" if v is None else f"{v:.1f}".replace(".", ",").replace("0,", ",", 1) if 0 < v < 1 else f"{v:.1f}".replace(".", ",")


def gerar_csv(horas: int = 48, lacunas_temp: dict[int, int] | None = None, chuva_vazia: set[int] | None = None) -> bytes:
    """Gera `horas` linhas a partir de 2025/01/01 00 UTC.

    lacunas_temp: {hora_inicial: tamanho} de temperaturas vazias.
    Radiação vem vazia à noite (como no arquivo real) e em kJ/m² de dia.
    """
    lacunas_temp = lacunas_temp or {}
    vazias = {h for ini, n in lacunas_temp.items() for h in range(ini, ini + n)}
    chuva_vazia = chuva_vazia or set()
    linhas = [";".join(COLUNAS_2025) + ";"]
    for h in range(horas):
        dia, hora = 1 + h // 24, h % 24
        temp = 22 + 5 * math.sin((hora - 9) / 24 * 2 * math.pi)
        # Sol em SC (UTC-3) entre ~08h e ~22h UTC no verão.
        rad = max(0.0, 2600 * math.sin((hora - 8) / 14 * math.pi)) if 9 <= hora <= 21 else None
        chuva = None if h in chuva_vazia else (0.8 if hora == 18 else 0.0)
        valores = [
            f"2025/01/{dia:02d}", f"{hora:02d}00 UTC", _br(chuva), "1005,2", "1005,6", "1004,9",
            _br(rad), None if h in vazias else _br(temp), "18,1", "27,0", "21,0", "18,5", "17,9", "90", "70",
            "80", "120", "6,1", "2,3",
        ]
        linhas.append(";".join("" if v is None else v for v in valores) + ";")
    return (METADADOS + "\n".join(linhas) + "\n").encode("latin-1")


@pytest.fixture
def csv_inmet():
    return gerar_csv

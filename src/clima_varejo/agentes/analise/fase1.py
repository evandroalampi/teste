"""Fase 1: análise de histórico, antes de qualquer modelo preditivo (seção 7).

Objetivo: descobrir quais variáveis climáticas geram sinal, por categoria e faixa climática.
Cuidados obrigatórios:
- controlar o clima NORMAL da região (anomalia em relação à climatologia local) antes de atribuir
  efeito ao tempo do dia, para não marcar categorias como sensíveis ao clima por engano;
- controlar sazonalidade, dia da semana, datas comerciais, desconto (promoção) e eventos de loja;
- separar o efeito da bandeira (varejo x atacarejo) do efeito do clima;
- medir volume, ticket médio e mix, não só volume;
- usar defasagens das variáveis climáticas.
"""

from __future__ import annotations

import pandas as pd


def anomalia(df: pd.DataFrame, coluna: str, chaves: list[str] = ("id_ponto",)) -> pd.Series:
    """Desvio em relação à média do mesmo ponto, mês e hora (climatologia simples do período)."""
    ref = df["data_hora_local"]
    grupos = [df[c] for c in chaves] + [ref.dt.month, ref.dt.hour]
    return df[coluna] - df.groupby(grupos)[coluna].transform("mean")


def defasagens(df: pd.DataFrame, coluna: str, horas: list[int], por: list[str]) -> pd.DataFrame:
    """Cópias deslocadas no tempo (positivas = passado, negativas = futuro/previsão)."""
    df = df.sort_values(por + ["data_hora_local"]).copy()
    for h in horas:
        sufixo = f"lag{h}h" if h > 0 else f"lead{-h}h"
        df[f"{coluna}_{sufixo}"] = df.groupby(por)[coluna].shift(h)
    return df

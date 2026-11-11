"""Orquestração do agente de clima: fonte -> regras de qualidade -> contrato.clima_hora."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ... import db
from ...config import settings
from ...dominio.clima import CHAVE_CLIMA_HORA, COLUNAS_CLIMA_HORA, FUSO_LOCAL, Fonte, kj_m2_para_w_m2
from . import qualidade
from .fontes import inmet


def normalizar_inmet(
    meta: inmet.MetadadosEstacao, dados: pd.DataFrame, versao_fonte: str, regras: dict
) -> pd.DataFrame:
    """Converte o CSV padronizado do INMET para o layout de contrato.clima_hora."""
    df = dados.copy()
    df["radiacao_w_m2"] = kj_m2_para_w_m2(df.pop("radiacao_kj_m2")) if "radiacao_kj_m2" in df else pd.NA
    df["flag_qualidade"] = pd.Series([None] * len(df), dtype="object")

    df = qualidade.zerar_radiacao_noturna(df, meta.latitude, meta.longitude)
    df = qualidade.interpolar_lacunas_curtas(df, "temperatura_c", regras["interpolar_temperatura_max_horas"])
    df = qualidade.marcar_fora_de_faixa(df, regras["faixas"])

    df["id_ponto"] = meta.codigo_wmo
    df["data_hora_local"] = df["data_hora_utc"].dt.tz_convert(FUSO_LOCAL).dt.tz_localize(None)
    df["fuso_horario"] = FUSO_LOCAL
    df["latitude"], df["longitude"], df["elevacao_m"] = meta.latitude, meta.longitude, meta.altitude_m
    df["fonte"] = Fonte.INMET.value
    df["versao_fonte"] = versao_fonte
    df["data_coleta"] = datetime.now(timezone.utc)
    for coluna in COLUNAS_CLIMA_HORA:
        if coluna not in df:
            df[coluna] = None
    return df[COLUNAS_CLIMA_HORA]


def ponto_inmet(meta: inmet.MetadadosEstacao) -> pd.DataFrame:
    return pd.DataFrame([{
        "id_ponto": meta.codigo_wmo, "fonte": Fonte.INMET.value, "nome": meta.nome,
        "latitude": meta.latitude, "longitude": meta.longitude, "elevacao_m": meta.altitude_m,
        "tipo": "estacao", "data_fundacao": meta.data_fundacao,
    }])


def ingerir_inmet(anos: list[int] | None = None, baixar: bool = True) -> list[dict]:
    """Carga histórica do INMET: baixa (opcional) e grava os pacotes anuais das estações do piloto."""
    cfg = settings()
    conf_inmet, regras = cfg.piloto["inmet"], cfg.piloto["qualidade"]
    periodo = cfg.piloto["piloto"]["periodo"]
    inicio = pd.Timestamp(periodo["inicio"], tz=FUSO_LOCAL)
    fim = pd.Timestamp(periodo["fim"], tz=FUSO_LOCAL) + pd.Timedelta(days=1)
    raw_dir: Path = cfg.data_dir / "raw" / "inmet"
    relatorio = []

    with db.conectar() as conn:
        for ano in anos or conf_inmet["anos"]:
            zip_path = (
                inmet.baixar_pacote_anual(ano, raw_dir, conf_inmet["url_pacote_anual"])
                if baixar else raw_dir / f"inmet_{ano}.zip"
            )
            for meta, dados in inmet.ler_pacote_anual(zip_path, conf_inmet["estacoes"]):
                completude = qualidade.checar_completude(dados, ano)
                df = normalizar_inmet(meta, dados, f"pacote_anual_{ano}", regras)
                df = df[(df["data_hora_utc"] >= inicio) & (df["data_hora_utc"] < fim)]
                db.upsert(conn, "apoio.ponto_climatico", ponto_inmet(meta), ["id_ponto"])
                n = db.upsert(conn, "contrato.clima_hora", df, CHAVE_CLIMA_HORA)
                relatorio.append({"estacao": meta.codigo_wmo, **completude, "gravadas": n})
            conn.commit()
    return relatorio

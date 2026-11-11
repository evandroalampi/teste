"""Conexão com o banco de clima local. Migrar para a nuvem = trocar CLIMA_DB_URL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import psycopg

from .config import RAIZ, settings


def conectar() -> psycopg.Connection:
    return psycopg.connect(settings().db_url)


def aplicar_migracoes() -> list[str]:
    aplicadas = []
    with conectar() as conn:
        for arquivo in sorted((RAIZ / "db" / "migrations").glob("*.sql")):
            conn.execute(arquivo.read_text(encoding="utf-8"))
            aplicadas.append(arquivo.name)
    return aplicadas


def upsert(conn: psycopg.Connection, tabela: str, df: pd.DataFrame, chave: list[str]) -> int:
    """Insere ou atualiza linhas de um DataFrame em `tabela` (ex.: 'contrato.clima_hora')."""
    if df.empty:
        return 0
    colunas = list(df.columns)
    atualizar = [c for c in colunas if c not in chave]
    sql = (
        f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join(['%s'] * len(colunas))}) "
        f"ON CONFLICT ({', '.join(chave)}) DO "
        + (f"UPDATE SET {', '.join(f'{c} = EXCLUDED.{c}' for c in atualizar)}" if atualizar else "NOTHING")
    )
    linhas = [tuple(None if pd.isna(v) else v for v in r) for r in df.itertuples(index=False)]
    with conn.cursor() as cur:
        cur.executemany(sql, linhas)
    return len(linhas)


def ler_sql(caminho: Path | str, **params) -> pd.DataFrame:
    with conectar() as conn:
        return pd.read_sql(Path(caminho).read_text(encoding="utf-8"), conn, params=params)

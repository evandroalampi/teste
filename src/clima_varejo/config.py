"""Configuração: variáveis de ambiente (.env) e recorte do piloto (config/piloto.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]


def _carregar_env(caminho: Path) -> None:
    """Lê um .env simples (CHAVE=valor) sem sobrescrever o ambiente."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


@dataclass(frozen=True)
class Settings:
    db_url: str
    lakehouse_url: str
    data_dir: Path
    piloto: dict


@lru_cache
def settings() -> Settings:
    _carregar_env(RAIZ / ".env")
    piloto = yaml.safe_load((RAIZ / "config" / "piloto.yaml").read_text(encoding="utf-8"))
    return Settings(
        db_url=os.environ.get("CLIMA_DB_URL", "postgresql://clima:clima@localhost:5432/clima_varejo"),
        lakehouse_url=os.environ.get("ROCK_LAKEHOUSE_URL", ""),
        data_dir=(RAIZ / os.environ.get("CLIMA_DATA_DIR", "data")).resolve(),
        piloto=piloto,
    )

"""Carga de vendas a partir do lakehouse da Rock.

Princípios: acesso só de leitura, sem cópia dos movimentos brutos; grava apenas os agregados
por hora. Carga inicial dos 24 meses e depois incremental por dataalteracao.
Pendências: credencial de leitura ao lakehouse (ou extrações em arquivo) e tabela de produtos.
"""

from __future__ import annotations

from pathlib import Path

AQUI = Path(__file__).parent
SQL_VENDAS_HORA = AQUI / "vendas_hora.sql"
SQL_FLUXO_LOJA_HORA = AQUI / "fluxo_loja_hora.sql"


def carregar_vendas(*_args, **_kwargs):
    raise NotImplementedError("Aguardando acesso de leitura ao lakehouse da Rock.")


def carregar_csv_extracao(caminho: Path):
    """Alternativa ao lakehouse: agregar um CSV de movimentos exportado pela Rock."""
    raise NotImplementedError("Aguardando amostra real de movimentos da Rede TOP.")

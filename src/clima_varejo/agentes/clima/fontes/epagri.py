"""Epagri/Ciram: rede estadual de SC (~259 estações ativas), dados horários. Seção 15.

Pendências antes de implementar:
- Cadastro no portal (o download exige login). URGENTE: janela móvel de 24 meses,
  novembro de 2024 está saindo da janela.
- Formato exato do CSV de download (validar com um arquivo real, como foi feito com o INMET).
- Termos de uso comercial.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê um CSV baixado do portal e devolve colunas no padrão de contrato.clima_hora."""
    raise NotImplementedError("Aguardando cadastro na Epagri/Ciram e um arquivo de exemplo.")

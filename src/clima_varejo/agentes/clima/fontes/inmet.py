"""INMET: pacote anual de dados históricos (seção 12 do documento de escopo).

Um ZIP por ano em portal.inmet.gov.br/dadoshistoricos, com um CSV por estação automática.
Regras confirmadas no arquivo de teste (A744, 2025):
- 8 linhas de metadados (chave;valor) e cabeçalho na linha 9;
- separador ';', decimal ',' (às vezes sem zero à esquerda: ',8'), encoding latin-1;
- cada linha termina com ';' -> coluna fantasma vazia, descartada;
- nulo = célula vazia; -9999 pode aparecer em outros anos -> os dois contam como nulo;
- Data AAAA/MM/DD e Hora "0000 UTC" (outros anos: AAAA-MM-DD e "00:00"); hora em UTC;
- radiação global em kJ/m², acumulada na hora; precipitação = acumulado da hora que termina em H.
Os nomes das colunas mudam entre anos: renomear por padrão de texto, nunca por posição.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

ENCODING = "latin-1"
LINHAS_METADADOS = 8
NULOS = ["", "-9999", "-9999,0", "-9999.0"]

# Padrões aplicados ao nome da coluna normalizado (sem acento, minúsculo, espaços simples).
# A ORDEM importa: os padrões mais específicos vêm antes.
PADROES_COLUNAS: list[tuple[str, str]] = [
    (r"^data", "data"),
    (r"^hora", "hora_utc"),
    (r"precipitac", "precipitacao_mm"),
    (r"pressao atmosferica max", "pressao_max_mb"),
    (r"pressao atmosferica min", "pressao_min_mb"),
    (r"pressao atmosferica", "pressao_mb"),
    (r"radiacao", "radiacao_kj_m2"),
    (r"bulbo seco", "temperatura_c"),
    (r"orvalho max", "orvalho_max_c"),
    (r"orvalho min", "orvalho_min_c"),
    (r"ponto de orvalho", "orvalho_c"),
    (r"temperatura maxima", "temp_max_c"),
    (r"temperatura minima", "temp_min_c"),
    (r"umidade rel\. max", "umidade_max_pct"),
    (r"umidade rel\. min", "umidade_min_pct"),
    (r"umidade relativa", "umidade_pct"),
    (r"vento, direcao", "vento_dir"),
    (r"vento, rajada", "rajada_ms"),
    (r"vento, velocidade", "vento_ms"),
]

CHAVES_METADADOS = {
    "regiao": "regiao",
    "uf": "uf",
    "estacao": "nome",
    "codigo (wmo)": "codigo_wmo",
    "latitude": "latitude",
    "longitude": "longitude",
    "altitude": "altitude_m",
    "data de fundacao": "data_fundacao",
}


@dataclass(frozen=True)
class MetadadosEstacao:
    codigo_wmo: str
    nome: str
    uf: str
    regiao: str
    latitude: float
    longitude: float
    altitude_m: float | None
    data_fundacao: date | None


def normalizar_texto(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def padronizar_coluna(nome_original: str) -> str | None:
    nome = normalizar_texto(nome_original)
    for padrao, destino in PADROES_COLUNAS:
        if re.search(padrao, nome):
            return destino
    return None


def _numero_br(valor: str) -> float | None:
    valor = valor.strip()
    if valor in NULOS:
        return None
    return float(valor.replace(",", "."))


def _data_fundacao(valor: str) -> date | None:
    valor = valor.strip()
    for formato in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return pd.to_datetime(valor, format=formato).date()
        except ValueError:
            continue
    return None


def ler_metadados(linhas: list[str]) -> MetadadosEstacao:
    brutos: dict[str, str] = {}
    for linha in linhas[:LINHAS_METADADOS]:
        if ":" not in linha:
            continue
        chave, _, valor = linha.partition(":")
        chave = normalizar_texto(chave)
        if chave in CHAVES_METADADOS:
            brutos[CHAVES_METADADOS[chave]] = valor.lstrip(";").strip().rstrip(";")
    return MetadadosEstacao(
        codigo_wmo=brutos["codigo_wmo"],
        nome=brutos.get("nome", ""),
        uf=brutos.get("uf", ""),
        regiao=brutos.get("regiao", ""),
        latitude=_numero_br(brutos["latitude"]),
        longitude=_numero_br(brutos["longitude"]),
        altitude_m=_numero_br(brutos.get("altitude_m", "")),
        data_fundacao=_data_fundacao(brutos.get("data_fundacao", "")),
    )


def _montar_data_hora_utc(data: pd.Series, hora: pd.Series) -> pd.Series:
    data_norm = data.str.strip().str.replace("-", "/", regex=False)
    hora_norm = hora.str.strip().str.replace(" UTC", "", regex=False).str.replace(":", "", regex=False)
    hora_norm = hora_norm.str.zfill(4)
    return pd.to_datetime(data_norm + " " + hora_norm, format="%Y/%m/%d %H%M", utc=True)


def ler_csv_estacao(conteudo: bytes | str) -> tuple[MetadadosEstacao, pd.DataFrame]:
    """Lê um CSV de estação do pacote anual e devolve metadados + dados com nomes padronizados.

    As unidades ficam como no arquivo (radiação em kJ/m²); a conversão é feita na ingestão.
    """
    texto = conteudo.decode(ENCODING) if isinstance(conteudo, bytes) else conteudo
    linhas = texto.splitlines()
    metadados = ler_metadados(linhas)

    bruto = pd.read_csv(
        io.StringIO("\n".join(linhas[LINHAS_METADADOS:])),
        sep=";",
        dtype=str,
        keep_default_na=False,
    )
    # Coluna fantasma criada pelo ';' no fim da linha.
    bruto = bruto.loc[:, [c for c in bruto.columns if c.strip() and not c.startswith("Unnamed")]]

    renomear, desconhecidas = {}, []
    for coluna in bruto.columns:
        destino = padronizar_coluna(coluna)
        if destino is None:
            desconhecidas.append(coluna)
        else:
            renomear[coluna] = destino
    if desconhecidas:
        raise ValueError(f"Colunas do INMET sem padrão conhecido: {desconhecidas}")
    bruto = bruto.rename(columns=renomear)

    df = pd.DataFrame({"data_hora_utc": _montar_data_hora_utc(bruto["data"], bruto["hora_utc"])})
    for coluna in bruto.columns.difference(["data", "hora_utc"]):
        df[coluna] = bruto[coluna].map(_numero_br).astype("float64")

    duplicadas = df["data_hora_utc"].duplicated()
    if duplicadas.any():
        raise ValueError(f"{metadados.codigo_wmo}: {duplicadas.sum()} horas duplicadas")
    return metadados, df.sort_values("data_hora_utc").reset_index(drop=True)


def listar_csvs_do_pacote(zip_path: Path, estacoes: list[str]) -> list[str]:
    """Nomes dos CSVs do pacote anual que pertencem às estações pedidas (ex.: A817)."""
    padrao = re.compile(r"_(" + "|".join(map(re.escape, estacoes)) + r")_", re.IGNORECASE)
    with zipfile.ZipFile(zip_path) as zf:
        return [n for n in zf.namelist() if n.lower().endswith(".csv") and padrao.search(n)]


def ler_pacote_anual(zip_path: Path, estacoes: list[str]):
    """Gera (metadados, dados) para cada estação pedida dentro do ZIP anual."""
    with zipfile.ZipFile(zip_path) as zf:
        for nome in listar_csvs_do_pacote(zip_path, estacoes):
            yield ler_csv_estacao(zf.read(nome))


def baixar_pacote_anual(ano: int, destino_dir: Path, url_modelo: str) -> Path:
    """Baixa o ZIP anual do INMET (rodar no Claude Code local: o portal não abre da nuvem)."""
    import requests

    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / f"inmet_{ano}.zip"
    if destino.exists():
        return destino
    with requests.get(url_modelo.format(ano=ano), stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(destino.with_suffix(".part"), "wb") as f:
            for bloco in resp.iter_content(chunk_size=1 << 20):
                f.write(bloco)
    destino.with_suffix(".part").rename(destino)
    return destino

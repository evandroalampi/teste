"""Linha de comando: `clima-varejo <comando>` (ou `python -m clima_varejo`)."""

from __future__ import annotations

import argparse
import json


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="clima-varejo")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("migrar", help="Cria/atualiza as tabelas no PostgreSQL local")

    p_inmet = sub.add_parser("inmet", help="Carga histórica do INMET (pacotes anuais)")
    p_inmet.add_argument("--anos", type=int, nargs="*", help="Padrão: anos do config/piloto.yaml")
    p_inmet.add_argument("--sem-download", action="store_true", help="Usar ZIPs já em data/raw/inmet")

    p_csv = sub.add_parser("inmet-validar", help="Valida um CSV de estação do INMET sem gravar")
    p_csv.add_argument("arquivo")

    args = parser.parse_args(argv)

    if args.comando == "migrar":
        from .db import aplicar_migracoes

        print("Migrações aplicadas:", ", ".join(aplicar_migracoes()))
    elif args.comando == "inmet":
        from .agentes.clima.ingestao import ingerir_inmet

        for linha in ingerir_inmet(args.anos, baixar=not args.sem_download):
            print(json.dumps(linha, ensure_ascii=False))
    elif args.comando == "inmet-validar":
        from pathlib import Path

        from .agentes.clima import qualidade
        from .agentes.clima.fontes import inmet

        meta, dados = inmet.ler_csv_estacao(Path(args.arquivo).read_bytes())
        ano = int(dados["data_hora_utc"].dt.year.mode().iat[0])
        print(json.dumps({
            "estacao": meta.codigo_wmo, "nome": meta.nome, "lat": meta.latitude, "lon": meta.longitude,
            "colunas": list(dados.columns), **qualidade.checar_completude(dados, ano),
            "nulos_por_coluna": {c: int(dados[c].isna().sum()) for c in dados.columns[1:]},
        }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

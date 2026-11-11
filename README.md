# Clima e Varejo

Cruza o clima por hora (temperatura, chuva, radiação solar) com as vendas por hora das lojas,
para medir como chuva e mudança de temperatura alteram volume, ticket médio e mix.
Piloto: **Rede TOP** (25 lojas Rede TOP + 6 Preceiro, SC), de **nov/2024 a out/2026**, rodando localmente.

Documento de escopo (fonte das decisões):
[Projeto Clima e Varejo – Escopo e Bibliografia](https://claude.ai/artifact/GEhWCxyiJTaMgQNqan14dP).

## Estrutura

```
config/piloto.yaml              recorte do piloto, estações INMET, hierarquia de fontes, regras de qualidade
db/migrations/                  esquema PostgreSQL (schemas `contrato` e `apoio`) e carga inicial
src/clima_varejo/
  config.py, db.py              .env + piloto.yaml; conexão e upsert
  dominio/clima.py              layout da tabela de clima unificada, fontes, flags, conversões
  agentes/
    clima/                      agente de ingestão climática (único que fala com fontes de clima)
      fontes/inmet.py           pacote anual do INMET: leitura, padronização de colunas por regex   [pronto]
      fontes/epagri.py          Epagri/Ciram                                                       [aguarda cadastro]
      fontes/cemaden.py         pluviômetros, reagregação de 10 min para hora                      [parcial]
      fontes/era5_land.py       grade ERA5-Land via Copernicus CDS                                 [aguarda conta]
      qualidade.py              radiação noturna = 0, interpolação de até 3 h, faixas, completude  [pronto]
      ingestao.py               fonte -> qualidade -> contrato.clima_hora                          [pronto p/ INMET]
    geografico/mapeamento.py    loja x ponto por variável (distância + hierarquia de fontes)       [pronto]
    transacional/               SQL de vendas_hora e fluxo_loja_hora sobre o lakehouse             [aguarda acesso]
    analise/                    base analítica (só tabelas do contrato) e utilitários da fase 1     [início]
    predicao/                   fase 2                                                             [futuro]
  cli.py                        comandos `migrar`, `inmet`, `inmet-validar`
tests/                          testes com CSV sintético no layout INMET 2025
docs/arquitetura.md             agentes, contrato de dados e fluxo
docs/pendencias.md              pendências do documento ligadas ao código
```

## Como rodar (máquina local)

```bash
cp .env.example .env
docker compose up -d                 # PostgreSQL 16 local (aplica db/migrations na 1ª subida)
pip install -e ".[dev]"
clima-varejo migrar                  # cria/atualiza tabelas (idempotente)
clima-varejo inmet                   # baixa os pacotes 2024-2026 e grava A817, A868, A851, A863
clima-varejo inmet-validar arquivo.CSV   # confere layout, completude e nulos de um CSV sem gravar
pytest
```

Os portais do governo (INMET, Epagri, Cemaden) não abrem do ambiente em nuvem: os downloads
rodam no Claude Code local.

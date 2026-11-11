# Pendências ligadas ao código

Revisão do documento de escopo de 06/11/2026, atualizada em 11/11/2026.

| Pendência | Quem | Onde no código | Estado |
| --- | --- | --- | --- |
| Baixar pacotes INMET 2024–2026 (A817, A868, A851, A863) | Claude Code local | `clima-varejo inmet` | Pronto para rodar |
| Conferir layout dos pacotes 2024 e 2026 | Claude Code local | `clima-varejo inmet-validar` | Pronto para rodar; coluna nova faz o parser falhar de propósito |
| Cadastro na Epagri/Ciram (**urgente**: nov/2024 saindo da janela) | Evandro | `fontes/epagri.py` | Aguarda cadastro e arquivo de exemplo |
| Conta no Copernicus CDS + token | Evandro | `fontes/era5_land.py`, `CDSAPI_KEY` | Aguarda conta |
| Mapear pluviômetros do Cemaden | Claude Code local | `fontes/cemaden.py`, `geografico/` | Agregação horária pronta |
| Tabela de produtos (categoria/departamento) | Evandro | `apoio.produto` | Aguarda exportação |
| Acesso de leitura ao lakehouse | Evandro | `transacional/carga.py` | SQL pronto, aguarda credencial |
| Amostra real de movimentos (fuso de dataconsumo) | Evandro | `transacional/vendas_hora.sql` | Aguarda amostra |
| Geocodificar GTOPINHO e Porto Belo; corrigir cidade de Presidente Getúlio | Banco local | `apoio.loja` | Aguarda carga do cadastro |
| Calendário de inaugurações e reformas | Claude | `db/migrations/002_seed_eventos_loja.sql` | 5 eventos; faltam Coloninha e Santa Terezinha |

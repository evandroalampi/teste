# Clima e Varejo — notas para o Claude Code

- Decisões de escopo vêm do documento "Projeto Clima e Varejo – Escopo e Bibliografia"
  (https://claude.ai/artifact/GEhWCxyiJTaMgQNqan14dP). Em caso de conflito, o documento vence.
- Código, nomes de tabelas e comentários em português, sem acento em identificadores.
- O agente de análise lê só `contrato.*`. Só os agentes de dados acessam fontes externas.
- A base da Rock é somente leitura; nunca copiar movimentos brutos para o banco local.
- Chave de loja sempre `idvarejista + idloja`. Clima sempre em UTC + hora local derivada.
- Nunca descartar registro de clima por qualidade: marcar em `flag_qualidade`.
- Testes: `pytest` (não precisam de banco). Banco local: `docker compose up -d` e `clima-varejo migrar`.

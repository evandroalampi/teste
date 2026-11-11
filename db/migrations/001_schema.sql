-- Projeto Clima e Varejo: esquema do banco local (prova de conceito).
-- Fonte: documento "Projeto Clima e Varejo - Escopo e Bibliografia", seções 10, 14, 16 e 17.
--
-- Contrato entre agentes (seção 10): o agente de análise lê APENAS três tabelas:
--   contrato.clima_hora   clima por hora e local
--   contrato.vendas_hora  vendas por loja, produto e hora
--   contrato.loja_ponto   mapeamento loja x ponto climático
-- As demais tabelas (schema "apoio") são de uso dos agentes de dados.
-- Só o agente de ingestão climática fala com fontes externas.

CREATE SCHEMA IF NOT EXISTS contrato;
CREATE SCHEMA IF NOT EXISTS apoio;

-- ---------------------------------------------------------------------------
-- Apoio: pontos climáticos (estações e células de grade)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apoio.ponto_climatico (
    id_ponto       text PRIMARY KEY,          -- código WMO (ex.: A817) ou id da célula da grade
    fonte          text NOT NULL,             -- INMET, EPAGRI, CEMADEN, ERA5_LAND, OPEN_METEO...
    nome           text,
    latitude       double precision NOT NULL,
    longitude      double precision NOT NULL,
    elevacao_m     double precision,
    tipo           text NOT NULL DEFAULT 'estacao' CHECK (tipo IN ('estacao', 'pluviometro', 'grade')),
    data_fundacao  date,
    ativo          boolean NOT NULL DEFAULT true
);

-- ---------------------------------------------------------------------------
-- Contrato 1: clima por hora e local (seção 14, tabela de clima unificada)
-- Tudo em UTC; radiação em W/m²; precipitação = acumulado da hora que termina em H.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contrato.clima_hora (
    id_ponto            text NOT NULL REFERENCES apoio.ponto_climatico (id_ponto),
    data_hora_utc       timestamptz NOT NULL,
    data_hora_local     timestamp NOT NULL,      -- America/Sao_Paulo (UTC-3), usada no cruzamento com vendas
    fuso_horario        text NOT NULL DEFAULT 'America/Sao_Paulo',
    latitude            double precision NOT NULL,
    longitude           double precision NOT NULL,
    elevacao_m          double precision,
    temperatura_c       real,
    temp_max_c          real,                    -- só INMET
    temp_min_c          real,                    -- só INMET
    sensacao_termica_c  real,                    -- só Open-Meteo / grade
    precipitacao_mm     real,
    radiacao_w_m2       real,
    umidade_pct         real,
    nebulosidade_pct    real,                    -- só grade
    vento_ms            real,
    rajada_ms           real,
    vento_dir           real,
    pressao_mb          real,
    fonte               text NOT NULL,           -- origem do registro
    versao_fonte        text NOT NULL,           -- pacote anual 2025, TEMPO, ERA5-Land...
    flag_qualidade      text,                    -- lacuna, interpolado, fora_faixa... (marcar, não descartar)
    data_coleta         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_ponto, data_hora_utc, fonte)
);
CREATE INDEX IF NOT EXISTS ix_clima_hora_local ON contrato.clima_hora (id_ponto, data_hora_local);

-- ---------------------------------------------------------------------------
-- Apoio: lojas (seção 17). Chave composta idvarejista + idloja.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apoio.loja (
    idvarejista      text NOT NULL,              -- redetop-indaial-sc | preceiro-indaial-sc
    idloja           integer NOT NULL,
    codigoexterno    text,                       -- possível chave alternativa (confirmar)
    nome             text NOT NULL,
    bandeira         text NOT NULL,              -- Rede TOP | Preceiro
    formato          text,                       -- Supermercado | Atacarejo
    endereco         text,
    bairro           text,
    cidade           text,
    uf               text NOT NULL DEFAULT 'SC',
    faixa_climatica  text CHECK (faixa_climatica IN ('litoral', 'medio_vale', 'alto_vale')),
    latitude         double precision,
    longitude        double precision,
    ativa            boolean NOT NULL DEFAULT true,
    no_piloto        boolean NOT NULL DEFAULT true,
    lojaglobal       boolean,                    -- significado a confirmar com o cadastro
    data_cadastro    date,                       -- datagravacao (cadastro, não inauguração)
    PRIMARY KEY (idvarejista, idloja)
);

-- ---------------------------------------------------------------------------
-- Contrato 2: mapeamento loja x ponto climático (seções 10 e 16)
-- O agente geográfico decide qual ponto atende cada loja EM CADA VARIÁVEL
-- (ex.: chuva do Cemaden, radiação do ERA5-Land). 'todas' = vale para tudo.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contrato.loja_ponto (
    idvarejista     text NOT NULL,
    idloja          integer NOT NULL,
    variavel        text NOT NULL DEFAULT 'todas',
    id_ponto        text NOT NULL REFERENCES apoio.ponto_climatico (id_ponto),
    fonte           text NOT NULL,
    distancia_km    double precision NOT NULL,
    data_inicio     date NOT NULL,
    PRIMARY KEY (idvarejista, idloja, variavel, data_inicio),
    FOREIGN KEY (idvarejista, idloja) REFERENCES apoio.loja (idvarejista, idloja)
);

-- ---------------------------------------------------------------------------
-- Contrato 3: vendas por loja, produto e hora (seção 17, proposta vendas_hora)
-- Agregado a partir da tabela de movimentos do lakehouse (leitura apenas, sem cópia do bruto).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contrato.vendas_hora (
    idvarejista      text NOT NULL,
    idloja           integer NOT NULL,
    data_hora_local  timestamp NOT NULL,         -- dataconsumo truncada na hora
    idproduto        bigint NOT NULL,
    quantidade       numeric NOT NULL,
    valor_bruto      numeric NOT NULL,           -- soma de valortotal
    valor_desconto   numeric NOT NULL DEFAULT 0, -- soma de valordescontoitem (controle de promoção)
    n_cupons         integer NOT NULL,           -- distintos numerocupom + identificacaopdv
    PRIMARY KEY (idvarejista, idloja, data_hora_local, idproduto),
    FOREIGN KEY (idvarejista, idloja) REFERENCES apoio.loja (idvarejista, idloja)
);

-- Fluxo de clientes por loja e hora (cupons e ticket médio): separa o efeito do clima
-- sobre o fluxo do efeito sobre o mix. É uma visão agregada de vendas_hora, mas os cupons
-- distintos da loja não se somam a partir das linhas por produto (um cupom tem vários
-- produtos), então o agente transacional grava este agregado junto com vendas_hora.
-- A confirmar: faz parte do contrato de vendas (mesma origem, mesmo agente).
CREATE TABLE IF NOT EXISTS contrato.fluxo_loja_hora (
    idvarejista      text NOT NULL,
    idloja           integer NOT NULL,
    data_hora_local  timestamp NOT NULL,
    n_cupons         integer NOT NULL,
    valor_bruto      numeric NOT NULL,
    valor_desconto   numeric NOT NULL DEFAULT 0,
    ticket_medio     numeric GENERATED ALWAYS AS (valor_bruto / NULLIF(n_cupons, 0)) STORED,
    PRIMARY KEY (idvarejista, idloja, data_hora_local),
    FOREIGN KEY (idvarejista, idloja) REFERENCES apoio.loja (idvarejista, idloja)
);

-- ---------------------------------------------------------------------------
-- Apoio: produtos (pendente: exportar categoria e departamento)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apoio.produto (
    idvarejista    text NOT NULL,
    idproduto      bigint NOT NULL,
    codigobarra    text,
    produto        text,
    categoria      text,
    departamento   text,
    PRIMARY KEY (idvarejista, idproduto)
);

-- ---------------------------------------------------------------------------
-- Apoio: eventos que mudam o patamar de vendas (inaugurações, reformas)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apoio.evento_loja (
    id             serial PRIMARY KEY,
    idvarejista    text NOT NULL,
    idloja         integer,                      -- preencher quando o cadastro for ligado
    loja_nome      text NOT NULL,
    data_evento    date,                         -- nulo quando a data é desconhecida
    precisao_data  text NOT NULL DEFAULT 'dia' CHECK (precisao_data IN ('dia', 'mes', 'desconhecida')),
    tipo           text NOT NULL,                -- inauguracao | reinauguracao | retrofit | obra
    descricao      text,
    fonte          text,
    UNIQUE (idvarejista, loja_nome, tipo)
);

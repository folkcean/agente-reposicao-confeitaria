-- =============================================================================
-- schema.sql: a "planta" do banco de demonstração do agente de reposição.
--
-- Este arquivo sozinho NÃO cria banco nenhum. Ele é só uma receita, lida pela
-- função criar_tabelas() em dados/conexao.py, que executa estes comandos dentro
-- do arquivo confeitaria.db (ou de um banco em memória, nos testes).
--
-- Cada tabela alimenta um SENSOR da matriz PEAS (o símbolo entre parênteses é
-- o nome do fato que o agente usa nas regras):
--   ingredientes        -> prazo de entrega (L), embalagem (B), perecível, vida útil (V)
--   lotes               -> estoque útil (E) e os avisos de validade (R11, R12)
--   produtos + receitas -> junto com vendas, dão o consumo por dia (c)
--   vendas              -> consumo por dia (c)
--   pedidos             -> quantidade a caminho (P)
-- =============================================================================

-- Liga a checagem de chaves estrangeiras (por padrão o SQLite vem desligado).
PRAGMA foreign_keys = ON;

-- Apaga as tabelas antigas, se existirem, para o "povoar" sempre começar do zero.
-- A ordem é a INVERSA das dependências: primeiro quem aponta para outras tabelas
-- (pedidos aponta para ingredientes, vendas aponta para produtos...).
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS vendas;
DROP TABLE IF EXISTS receitas;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS lotes;
DROP TABLE IF EXISTS ingredientes;

-- Cadastro de cada insumo da confeitaria.
CREATE TABLE ingredientes (
    id                  INTEGER PRIMARY KEY,           -- número único do ingrediente
    nome                TEXT    NOT NULL UNIQUE,       -- "Farinha de trigo"; não pode repetir
    unidade             TEXT    NOT NULL,              -- "kg", "un", "g", "lata", "caixa"...
    perecivel           INTEGER NOT NULL CHECK (perecivel IN (0, 1)),  -- SQLite não tem bool: 0 = não, 1 = sim
    vida_util_dias      INTEGER,                       -- V; fica vazio (NULL) se não for perecível
    embalagem           REAL    NOT NULL CHECK (embalagem > 0),        -- B: ex. 25 para saco de 25 kg
    prazo_entrega_dias  INTEGER NOT NULL CHECK (prazo_entrega_dias >= 0) -- L: dias que o fornecedor leva
);

-- Cada entrada de mercadoria. O estoque de um ingrediente é a soma dos seus lotes.
CREATE TABLE lotes (
    id              INTEGER PRIMARY KEY,
    ingrediente_id  INTEGER NOT NULL REFERENCES ingredientes(id),  -- de qual ingrediente é o lote
    quantidade      REAL    NOT NULL CHECK (quantidade >= 0),      -- quanto ainda resta do lote
    validade        TEXT    NOT NULL            -- data no formato ISO AAAA-MM-DD (SQLite guarda datas como texto)
);

-- O que a confeitaria vende.
CREATE TABLE produtos (
    id    INTEGER PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE                  -- "Bolo de chocolate"
);

-- Ficha técnica: quanto de cada ingrediente vai em UMA unidade de cada produto.
CREATE TABLE receitas (
    produto_id      INTEGER NOT NULL REFERENCES produtos(id),
    ingrediente_id  INTEGER NOT NULL REFERENCES ingredientes(id),
    quantidade      REAL    NOT NULL CHECK (quantidade > 0),       -- ex.: 0.3 kg de farinha por bolo
    PRIMARY KEY (produto_id, ingrediente_id)    -- cada ingrediente aparece uma vez por receita
);

-- Quantas unidades de cada produto foram vendidas em cada dia.
CREATE TABLE vendas (
    id          INTEGER PRIMARY KEY,
    produto_id  INTEGER NOT NULL REFERENCES produtos(id),
    data        TEXT    NOT NULL,               -- data ISO AAAA-MM-DD
    quantidade  INTEGER NOT NULL CHECK (quantidade > 0)
);

-- Compras feitas ao fornecedor. Só as 'pendente' contam como "a caminho" (P).
CREATE TABLE pedidos (
    id              INTEGER PRIMARY KEY,
    ingrediente_id  INTEGER NOT NULL REFERENCES ingredientes(id),
    quantidade      REAL    NOT NULL CHECK (quantidade > 0),
    data_pedido     TEXT    NOT NULL,           -- data ISO AAAA-MM-DD
    status          TEXT    NOT NULL CHECK (status IN ('pendente', 'recebido'))
);

-- Índices: deixam mais rápidas as consultas que o repositório faz o tempo todo
-- (vendas por data e lotes por ingrediente). Com poucos dados não faz diferença,
-- mas é a prática correta para quando o banco crescer.
CREATE INDEX idx_vendas_data ON vendas(data);
CREATE INDEX idx_lotes_ingrediente ON lotes(ingrediente_id);
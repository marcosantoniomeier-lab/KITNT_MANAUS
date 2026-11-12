"""Criação do esquema do banco de dados e do usuário administrador inicial."""
import hashlib
import hmac
import os

from database.conexao import Conexao

ITERACOES_HASH = 100_000


def gerar_hash_senha(senha):
    """Gera 'salt$hash' usando PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES_HASH)
    return f"{salt.hex()}${derivada.hex()}"


def verificar_senha(senha, senha_hash):
    try:
        salt_hex, hash_hex = senha_hash.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    derivada = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES_HASH)
    return hmac.compare_digest(derivada.hex(), hash_hex)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS estudantes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    cpf         TEXT NOT NULL UNIQUE CHECK (length(cpf) = 11),
    telefone    TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    curso       TEXT NOT NULL,
    instituicao TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kitnets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    endereco      TEXT NOT NULL,
    bairro        TEXT NOT NULL,
    quartos       INTEGER NOT NULL DEFAULT 1 CHECK (quartos >= 1),
    valor_aluguel REAL NOT NULL CHECK (valor_aluguel > 0),
    status        TEXT NOT NULL DEFAULT 'Disponível'
                  CHECK (status IN ('Disponível', 'Alugada', 'Em manutenção')),
    UNIQUE (endereco, bairro)
);

CREATE TABLE IF NOT EXISTS locacoes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    estudante_id     INTEGER NOT NULL
                     REFERENCES estudantes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    kitnet_id        INTEGER NOT NULL
                     REFERENCES kitnets(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    data_inicio      TEXT NOT NULL,
    data_fim         TEXT,
    valor_contratado REAL NOT NULL CHECK (valor_contratado > 0),
    status           TEXT NOT NULL DEFAULT 'Ativa'
                     CHECK (status IN ('Ativa', 'Encerrada', 'Cancelada')),
    CHECK (data_fim IS NULL OR data_fim >= data_inicio)
);

-- Regras de negócio garantidas pelo banco:
-- uma kitnet só pode ter UMA locação ativa e um estudante só pode ter UMA locação ativa.
CREATE UNIQUE INDEX IF NOT EXISTS ux_locacao_ativa_kitnet
    ON locacoes(kitnet_id) WHERE status = 'Ativa';
CREATE UNIQUE INDEX IF NOT EXISTS ux_locacao_ativa_estudante
    ON locacoes(estudante_id) WHERE status = 'Ativa';

CREATE TABLE IF NOT EXISTS pagamentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    locacao_id     INTEGER NOT NULL
                   REFERENCES locacoes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    valor          REAL NOT NULL CHECK (valor > 0),
    vencimento     TEXT NOT NULL,
    data_pagamento TEXT,
    status         TEXT NOT NULL DEFAULT 'Pendente'
                   CHECK (status IN ('Pendente', 'Pago', 'Atrasado')),
    CHECK (
        (status = 'Pago' AND data_pagamento IS NOT NULL) OR
        (status <> 'Pago' AND data_pagamento IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS manutencoes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    kitnet_id INTEGER NOT NULL
              REFERENCES kitnets(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
    categoria TEXT NOT NULL,
    custo     REAL NOT NULL DEFAULT 0 CHECK (custo >= 0),
    status    TEXT NOT NULL DEFAULT 'Aberta'
              CHECK (status IN ('Aberta', 'Em andamento', 'Concluída', 'Cancelada'))
);

CREATE TABLE IF NOT EXISTS despesas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kitnet_id     INTEGER NOT NULL
                  REFERENCES kitnets(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    manutencao_id INTEGER
                  REFERENCES manutencoes(id) ON UPDATE CASCADE ON DELETE SET NULL,
    descricao     TEXT NOT NULL,
    categoria     TEXT NOT NULL,
    valor         REAL NOT NULL CHECK (valor > 0),
    data          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT NOT NULL,
    login      TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil     TEXT NOT NULL DEFAULT 'Funcionário'
               CHECK (perfil IN ('Administrador', 'Funcionário'))
);

CREATE TABLE IF NOT EXISTS historico (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL
               REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    operacao   TEXT NOT NULL,
    descricao  TEXT NOT NULL,
    data_hora  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS ix_locacoes_estudante   ON locacoes(estudante_id);
CREATE INDEX IF NOT EXISTS ix_locacoes_kitnet      ON locacoes(kitnet_id);
CREATE INDEX IF NOT EXISTS ix_pagamentos_locacao   ON pagamentos(locacao_id);
CREATE INDEX IF NOT EXISTS ix_pagamentos_vencim    ON pagamentos(vencimento);
CREATE INDEX IF NOT EXISTS ix_manutencoes_kitnet   ON manutencoes(kitnet_id);
CREATE INDEX IF NOT EXISTS ix_despesas_kitnet      ON despesas(kitnet_id);
CREATE INDEX IF NOT EXISTS ix_historico_usuario    ON historico(usuario_id);
"""


def criar_tabelas():
    """Cria o banco (se não existir), todas as tabelas e o usuário admin inicial."""
    with Conexao.transacao() as conn:
        conn.executescript(SCHEMA_SQL)
        _criar_usuario_padrao(conn)


def _criar_usuario_padrao(conn):
    total = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if total == 0:
        conn.execute(
            "INSERT INTO usuarios (nome, login, senha_hash, perfil) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin", gerar_hash_senha("admin123"), "Administrador"),
        )
"""Conexão com o banco SQLite e criação das tabelas.

Para que serve
--------------
Concentra num lugar só o "como abrir o banco", para o resto do projeto não
repetir esse código. Tem duas funções:

- abrir_conexao(caminho): abre (ou cria, se não existir) o arquivo do banco.
- criar_tabelas(conn):    executa o schema.sql, apagando e recriando as tabelas.

Como foi feito
--------------
Usa só o módulo sqlite3, que já vem com o Python: não há nada para instalar e
nenhum servidor para ligar. O banco inteiro é um único arquivo (confeitaria.db).
O caminho especial ":memory:" cria um banco temporário na memória, que some
quando a conexão fecha. Os testes usam isso para não deixar arquivos para trás.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

# Caminho do schema.sql. Path(__file__) é o caminho DESTE arquivo (conexao.py);
# .with_name("schema.sql") troca só o nome do arquivo, mantendo a mesma pasta.
# Assim funciona não importa de qual pasta o programa for executado.
SCHEMA = Path(__file__).with_name("schema.sql")

# Nome do arquivo de banco usado quando ninguém informa outro (main.py usa).
BANCO_PADRAO = "confeitaria.db"


def abrir_conexao(caminho: str = BANCO_PADRAO) -> sqlite3.Connection:
    """Abre (ou cria) o banco e devolve a conexão já configurada."""
    conn = sqlite3.connect(caminho)
    # row_factory = sqlite3.Row faz cada linha do resultado se comportar como um
    # dicionário: dá para escrever linha["nome"] em vez de linha[1].
    conn.row_factory = sqlite3.Row
    # O SQLite só checa as chaves estrangeiras (REFERENCES) se isto for ligado
    # em CADA conexão aberta.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_tabelas(conn: sqlite3.Connection) -> None:
    """Apaga e recria todas as tabelas a partir de schema.sql."""
    # executescript roda vários comandos SQL de uma vez (o arquivo inteiro).
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()  # confirma a gravação no banco
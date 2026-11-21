"""Grava os cenários de dados/cenarios.py dentro do banco.

Para que serve
--------------
Transforma as listas de cenarios.py em linhas nas tabelas do banco, para que o
repositório (os sensores) tenha o que ler. É chamado pelo comando:

    python main.py povoar --hoje 2026-11-20

e também pelos testes, com um banco em memória:

    conn = abrir_conexao(":memory:")
    povoar(conn, date(2026, 11, 20))

Como foi feito
--------------
1. Recria as tabelas (apaga tudo o que havia).
2. Insere ingredientes, produtos e receitas.
3. Para cada produto, insere UMA venda por dia nos 28 dias ANTES de hoje
   (de ontem até 28 dias atrás). Hoje não entra, porque o dia ainda não acabou.
4. Converte "dias a partir de hoje" em datas reais para lotes e pedidos.

`executemany` insere várias linhas com um único comando. Os pontos de
interrogação (?) são preenchidos pelo sqlite3 com os valores, na ordem. Isso é
mais seguro do que montar o texto do SQL à mão.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from dados import cenarios
from dados.conexao import criar_tabelas


def povoar(conn: sqlite3.Connection, hoje: date) -> None:
    """Apaga tudo, recria as tabelas e grava os 10 cenários."""
    criar_tabelas(conn)

    # Ingredientes. int(p) converte True/False em 1/0, porque o SQLite não tem bool.
    conn.executemany(
        "INSERT INTO ingredientes (id, nome, unidade, perecivel, vida_util_dias, embalagem, prazo_entrega_dias) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(i, n, u, int(p), v, b, l) for (i, n, u, p, v, b, l) in cenarios.INGREDIENTES],
    )

    for pid, nome, por_dia, receita in cenarios.PRODUTOS:
        # O produto.
        conn.execute("INSERT INTO produtos (id, nome) VALUES (?, ?)", (pid, nome))
        # A ficha técnica: uma linha por ingrediente da receita.
        conn.executemany(
            "INSERT INTO receitas (produto_id, ingrediente_id, quantidade) VALUES (?, ?, ?)",
            [(pid, iid, q) for iid, q in receita.items()],
        )
        # As vendas: d = 1 é ontem, d = 28 é 28 dias atrás.
        # .isoformat() transforma a data em texto "AAAA-MM-DD".
        conn.executemany(
            "INSERT INTO vendas (produto_id, data, quantidade) VALUES (?, ?, ?)",
            [
                (pid, (hoje - timedelta(days=d)).isoformat(), por_dia)
                for d in range(1, cenarios.JANELA_DIAS + 1)
            ],
        )

    # Lotes: validade = hoje + dias (dias negativos dão uma data no passado = vencido).
    conn.executemany(
        "INSERT INTO lotes (ingrediente_id, quantidade, validade) VALUES (?, ?, ?)",
        [(iid, q, (hoje + timedelta(days=d)).isoformat()) for iid, q, d in cenarios.LOTES],
    )

    # Pedidos: data_pedido = hoje − dias.
    conn.executemany(
        "INSERT INTO pedidos (ingrediente_id, quantidade, data_pedido, status) VALUES (?, ?, ?, ?)",
        [(iid, q, (hoje - timedelta(days=d)).isoformat(), st) for iid, q, d, st in cenarios.PEDIDOS],
    )

    conn.commit()  # só agora tudo fica gravado de verdade
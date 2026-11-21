"""RepositorioSQLite: os SENSORES do agente.

Para que serve
--------------
É a ponte entre o banco e o agente. O agente pede os ingredientes por
dois métodos definidos no contrato (agente/dominio/repositorio.py):

    listar_ingredientes(hoje)          -> lista de Ingrediente
    buscar_ingrediente(id, hoje)       -> um Ingrediente ou None

Esta classe implementa esses dois métodos lendo o SQLite. Para cada linha da
tabela `ingredientes`, ela monta um objeto Ingrediente com:

- consumo_diario (c): soma de (vendas × receita) nos últimos 28 dias, SEM contar
  hoje, dividida por 28;
- lotes: todos os lotes com quantidade > 0, INCLUSIVE os vencidos. Quem decide
  descartá-los é a regra R12 do agente, não o banco;
- a_caminho (P): soma dos pedidos com status 'pendente'.

O que NÃO entra aqui
--------------------
Nenhuma regra de negócio: nada de folga, nível mínimo ou "precisa comprar".
Este arquivo só LÊ e MONTA dados. Se um dia o agente for ligado ao banco real
do sistema, basta escrever outra classe com os mesmos dois métodos.

Como foi feito
--------------
A classe herda de RepositorioEstoque (uma classe abstrata). Se faltar algum dos
dois métodos, o Python não deixa criar o objeto: o contrato fica garantido.
As consultas SQL ficam em constantes no topo, para serem lidas e testadas à parte.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from agente.dominio.modelos import Ingrediente, Lote
from agente.dominio.repositorio import RepositorioEstoque

# Consumo total de UM ingrediente num intervalo de datas.
# Para cada venda, multiplica a quantidade vendida pela quantidade do ingrediente
# na receita daquele produto, e soma tudo.
# COALESCE(..., 0) troca o "nada" (NULL) por 0 quando o ingrediente não tem vendas.
# A condição "data >= início AND data < hoje" pega exatamente os 28 dias anteriores.
SQL_CONSUMO = """
    SELECT COALESCE(SUM(v.quantidade * r.quantidade), 0) AS total
    FROM vendas v
    JOIN receitas r ON r.produto_id = v.produto_id
    WHERE r.ingrediente_id = ? AND v.data >= ? AND v.data < ?
"""

# Lotes de um ingrediente que ainda têm alguma quantidade, do que vence antes
# para o que vence depois.
SQL_LOTES = """
    SELECT id, quantidade, validade FROM lotes
    WHERE ingrediente_id = ? AND quantidade > 0
    ORDER BY validade
"""

# Quanto deste ingrediente já foi pedido e ainda não chegou.
SQL_A_CAMINHO = """
    SELECT COALESCE(SUM(quantidade), 0) AS total FROM pedidos
    WHERE ingrediente_id = ? AND status = 'pendente'
"""


class RepositorioSQLite(RepositorioEstoque):
    """Lê ingredientes, vendas, lotes e pedidos de um banco SQLite."""

    def __init__(self, conn: sqlite3.Connection, janela_dias: int = 28) -> None:
        # janela_dias: quantos dias de vendas entram na média de consumo.
        if janela_dias <= 0:
            raise ValueError("janela_dias deve ser maior que zero")
        self.conn = conn
        self.janela_dias = janela_dias

    # ------------------------------------------------------------------
    # Os dois métodos exigidos pelo contrato (RepositorioEstoque)
    # ------------------------------------------------------------------
    def listar_ingredientes(self, hoje: date) -> list[Ingrediente]:
        """Todos os ingredientes, cada um com os dados calculados até `hoje`."""
        linhas = self.conn.execute("SELECT * FROM ingredientes ORDER BY id").fetchall()
        return [self._montar(linha, hoje) for linha in linhas]

    def buscar_ingrediente(self, ingrediente_id: int, hoje: date) -> Ingrediente | None:
        """Um ingrediente pelo id, ou None se não existir."""
        linha = self.conn.execute(
            "SELECT * FROM ingredientes WHERE id = ?", (ingrediente_id,)
        ).fetchone()
        return None if linha is None else self._montar(linha, hoje)

    # ------------------------------------------------------------------
    # Extra (não faz parte do contrato): usado pelo comando "explicar"
    # ------------------------------------------------------------------
    def buscar_por_nome(self, nome: str, hoje: date) -> Ingrediente | None:
        """Busca sem diferenciar maiúsculas e aceita parte do nome ('farinha')."""
        linha = self.conn.execute(
            # LIKE com % dos dois lados = "contém". lower() nos dois lados ignora maiúsculas.
            "SELECT * FROM ingredientes WHERE lower(nome) LIKE lower(?) ORDER BY id LIMIT 1",
            (f"%{nome}%",),
        ).fetchone()
        return None if linha is None else self._montar(linha, hoje)

    # ------------------------------------------------------------------
    # Os sensores, um método para cada dado
    # ------------------------------------------------------------------
    def consumo_diario(self, ingrediente_id: int, hoje: date) -> float:
        """c = consumo total nos últimos `janela_dias` dias ÷ `janela_dias`."""
        inicio = hoje - timedelta(days=self.janela_dias)
        total = self.conn.execute(
            SQL_CONSUMO, (ingrediente_id, inicio.isoformat(), hoje.isoformat())
        ).fetchone()["total"]
        # round(..., 3) evita valores como 4.999999999 por causa do ponto flutuante.
        return round(total / self.janela_dias, 3)

    def lotes(self, ingrediente_id: int) -> tuple[Lote, ...]:
        """Os lotes do ingrediente, convertendo a validade de texto para data."""
        return tuple(
            Lote(l["id"], l["quantidade"], date.fromisoformat(l["validade"]))
            for l in self.conn.execute(SQL_LOTES, (ingrediente_id,))
        )

    def a_caminho(self, ingrediente_id: int) -> float:
        """P = soma dos pedidos pendentes."""
        return float(self.conn.execute(SQL_A_CAMINHO, (ingrediente_id,)).fetchone()["total"])

    def _montar(self, linha: sqlite3.Row, hoje: date) -> Ingrediente:
        """Junta o cadastro com os três sensores num objeto Ingrediente do contrato."""
        iid = linha["id"]
        return Ingrediente(
            id=iid,
            nome=linha["nome"],
            unidade=linha["unidade"],
            consumo_diario=self.consumo_diario(iid, hoje),
            prazo_entrega_dias=linha["prazo_entrega_dias"],
            embalagem=linha["embalagem"],
            perecivel=bool(linha["perecivel"]),   # 0/1 do banco vira False/True
            vida_util_dias=linha["vida_util_dias"],
            a_caminho=self.a_caminho(iid),
            lotes=self.lotes(iid),
        )
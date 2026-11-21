"""Testes dos sensores, isto é, do RepositorioSQLite (tarefa B4).

Para que serve
--------------
Confere se os dados que chegam ao agente estão certos ANTES de o agente usá-los.
Se um destes testes falhar, o problema está no banco ou nas consultas, e não
nas regras.

Como foi feito
--------------
A fixture `repo` cria um banco em memória (":memory:"), povoa com os cenários e
entrega o repositório pronto. Cada teste recebe um banco novo e limpo.
A fixture `hoje` (data fixa 2026-11-20) vem de tests/conftest.py.
"""
import pytest

from dados.conexao import abrir_conexao
from dados.povoar import povoar
from dados.repositorio_sqlite import RepositorioSQLite


@pytest.fixture
def repo(hoje):
    conn = abrir_conexao(":memory:")
    povoar(conn, hoje)
    yield RepositorioSQLite(conn)   # o teste roda aqui
    conn.close()                    # e depois a conexão é fechada


# parametrize roda o MESMO teste 10 vezes, uma para cada par (id, consumo esperado).
@pytest.mark.parametrize("iid, esperado", [(1, 5), (2, 2), (3, 30), (4, 4), (5, 1), (6, 6),
                                           (7, 3), (8, 4), (9, 100), (10, 0)])
def test_consumo_diario(repo, hoje, iid, esperado):
    # pytest.approx compara números com uma pequena tolerância de ponto flutuante.
    assert repo.consumo_diario(iid, hoje) == pytest.approx(esperado)


def test_venda_de_hoje_nao_entra_na_media(repo, hoje):
    # Uma venda absurda hoje não pode mudar a média, porque o dia ainda não acabou.
    repo.conn.execute("INSERT INTO vendas (produto_id, data, quantidade) VALUES (1, ?, 1000)", (hoje.isoformat(),))
    assert repo.consumo_diario(1, hoje) == pytest.approx(5)


def test_a_caminho_ignora_pedido_recebido(repo):
    assert repo.a_caminho(3) == 300   # ovos: pedido pendente conta
    assert repo.a_caminho(1) == 0     # farinha: o pedido já foi recebido, não conta


def test_lotes_incluem_vencidos(repo, hoje):
    # O lote vencido do morango precisa chegar ao agente para a regra R12 avisar.
    morango = repo.buscar_ingrediente(7, hoje)
    assert sorted(l.dias_para_vencer(hoje) for l in morango.lotes) == [-1, 3]


def test_listar_e_buscar(repo, hoje):
    assert len(repo.listar_ingredientes(hoje)) == 10
    assert repo.buscar_ingrediente(99, hoje) is None
    assert repo.buscar_por_nome("FARINHA", hoje).id == 1


def test_campos_do_cadastro(repo, hoje):
    manteiga = repo.buscar_ingrediente(2, hoje)
    assert (manteiga.perecivel, manteiga.vida_util_dias, manteiga.embalagem, manteiga.prazo_entrega_dias) == (True, 10, 5, 2)
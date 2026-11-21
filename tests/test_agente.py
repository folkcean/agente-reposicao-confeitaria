"""Testes do agente completo com repositório em memória.
"""
import pytest

from agente.agente import AgenteReposicao
from agente.dominio.recomendacao import Situacao
from agente.dominio.repositorio import RepositorioMemoria


@pytest.fixture
def agente(fazer_ingrediente):
    return AgenteReposicao(RepositorioMemoria([
        fazer_ingrediente(id_ingrediente=1, nome="Farinha", consumo_diario=5, prazo_entrega_dias=3,
                          embalagem=25, lotes=[(22, 120)]),
        fazer_ingrediente(id_ingrediente=2, nome="Manteiga", consumo_diario=2, prazo_entrega_dias=2,
                          embalagem=5, perecivel=True, vida_util_dias=10, lotes=[(4, 2), (2, 9)]),
        fazer_ingrediente(id_ingrediente=3, nome="Ovos", consumo_diario=30, prazo_entrega_dias=1,
                          embalagem=30, perecivel=True, vida_util_dias=20, a_caminho=300, lotes=[(40, 15)],
                          unidade="un"),
    ]))


def test_farinha(agente, hoje):
    recomendacao = agente.avaliar_ingrediente(1, hoje)
    assert (recomendacao.situacao, recomendacao.sugestao_compra) == (Situacao.REPOR, 50)


def test_manteiga(agente, hoje):
    recomendacao = agente.avaliar_ingrediente(2, hoje)
    assert (recomendacao.situacao, recomendacao.sugestao_compra) == (Situacao.REPOR, 20)
    assert any("use primeiro" in aviso for aviso in recomendacao.avisos)


def test_ovos_nao_compra_por_causa_do_pedido(agente, hoje):
    recomendacao = agente.avaliar_ingrediente(3, hoje)
    assert recomendacao.situacao == Situacao.CRITICO
    assert recomendacao.sugestao_compra is None
    assert any("a caminho" in aviso for aviso in recomendacao.avisos)


def test_lista_ordenada_por_urgencia(agente, hoje):
    assert [recomendacao.ingrediente for recomendacao in agente.avaliar_todos(hoje)] == [
        "Ovos", "Farinha", "Manteiga"]


def test_reagir_reavalia_so_os_afetados(agente, hoje):
    assert [recomendacao.ingrediente_id for recomendacao in agente.reagir([2, 2], hoje)] == [2]


def test_explicacao_chega_aos_sensores(agente, hoje):
    explicacao = agente.explicar(1, hoje)
    for trecho_esperado in ("R10", "R9", "R6", "R4", "sensor", "N = c × L + F"):
        assert trecho_esperado in explicacao


def test_ingrediente_inexistente(agente, hoje):
    with pytest.raises(KeyError):
        agente.avaliar_ingrediente(99, hoje)
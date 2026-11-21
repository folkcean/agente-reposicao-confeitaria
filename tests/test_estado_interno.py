"""Testes do estado interno: as três contas e o estoque útil."""
import pytest

from agente.dominio.modelos import Parametros
from agente.estado.estado_interno import EstadoInterno


def test_contas_da_farinha(fazer_ingrediente, hoje):
    farinha = fazer_ingrediente(consumo_diario=5, prazo_entrega_dias=3, embalagem=25, lotes=[(22, 120)])
    estado_interno = EstadoInterno(farinha, Parametros(), hoje)
    assert (estado_interno.E, estado_interno.F, estado_interno.N, estado_interno.Q) == (22, 10, 25, 38)


def test_lote_vencido_nao_conta_no_estoque(fazer_ingrediente, hoje):
    morango = fazer_ingrediente(consumo_diario=3, prazo_entrega_dias=1, lotes=[(7, 3), (2, -1), (5, 0)])
    assert EstadoInterno(morango, Parametros(), hoje).E == 7   # vence hoje (0) também não conta


def test_pedido_a_caminho_entra_em_Q(fazer_ingrediente, hoje):
    ovos = fazer_ingrediente(consumo_diario=30, prazo_entrega_dias=1, lotes=[(40, 15)], a_caminho=300)
    assert EstadoInterno(ovos, Parametros(), hoje).Q == -40


def test_parametros_mudam_as_contas(fazer_ingrediente, hoje):
    farinha = fazer_ingrediente(consumo_diario=5, prazo_entrega_dias=3, lotes=[(22, 120)])
    estado_interno = EstadoInterno(farinha, Parametros(dias_folga=4, dias_cobertura=10), hoje)
    assert (estado_interno.F, estado_interno.N, estado_interno.Q) == (20, 35, 63)


def test_memoria_tem_todos_os_fatos_com_origem(fazer_ingrediente, hoje):
    memoria = EstadoInterno(fazer_ingrediente(lotes=[(22, 120)]), Parametros(), hoje).para_memoria()
    for nome_do_fato in ("c", "L", "P", "B", "perecivel", "lotes", "C", "A", "E", "F", "N", "Q"):
        assert nome_do_fato in memoria
    assert memoria.fato("c").origem.startswith("sensor")
    assert memoria.fato("N").dependencias == ("c", "L", "F")


def test_sem_ponto_flutuante_estranho(fazer_ingrediente, hoje):
    estado_interno = EstadoInterno(fazer_ingrediente(consumo_diario=0.1, prazo_entrega_dias=4,
                                                     lotes=[(1, 100)]), Parametros(), hoje)
    assert estado_interno.N == 0.6


def test_folga_zero_e_recusada():
    with pytest.raises(ValueError):
        Parametros(dias_folga=0)
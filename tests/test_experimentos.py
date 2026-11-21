"""Testes da simulação de desempenho (experimentos/simulacao.py).

Rodam poucas repetições para ficar rápidos. Conferem que a simulação é
reprodutível e que, no cenário normal, o agente supera as duas políticas
de comparação na medida principal (dias em ruptura) sem desperdiçar mais.
"""
from experimentos.simulacao import (
    CENARIOS, PoliticaAgente, PoliticaIfElse, PoliticaOperador, _receitas, resumir, simular,
)

NORMAL = CENARIOS[0]


def _rodar(politica, rep=3):
    return resumir([simular(politica, NORMAL, s) for s in range(rep)])


def test_simulacao_e_reprodutivel():
    a = _rodar(PoliticaAgente(), rep=2)
    b = _rodar(PoliticaAgente(), rep=2)
    assert a == b


def test_agente_tem_menos_ruptura_que_as_alternativas():
    nominal = _receitas()
    agente = _rodar(PoliticaAgente())
    if_else = _rodar(PoliticaIfElse(nominal))
    operador = _rodar(PoliticaOperador(nominal))
    assert agente["dias_ruptura"] < if_else["dias_ruptura"]
    assert agente["dias_ruptura"] < operador["dias_ruptura"]


def test_agente_desperdica_menos_que_o_if_else():
    agente = _rodar(PoliticaAgente())
    if_else = _rodar(PoliticaIfElse(_receitas()))
    assert agente["desperdicio"] < if_else["desperdicio"]
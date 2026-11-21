"""Testes do motor de inferência"""
import random

import pytest

from agente.conhecimento.base import BaseDeConhecimento
from agente.conhecimento.fatos import FatoJaExisteErro, MemoriaDeTrabalho
from agente.conhecimento.regra import Regra
from agente.conhecimento.regras_reposicao import REGRAS_REPOSICAO
from agente.dominio.modelos import Parametros
from agente.estado.estado_interno import EstadoInterno
from agente.inferencia.motor import MotorDeInferencia


def rodar_motor(ingrediente, hoje, regras=REGRAS_REPOSICAO):
    memoria = EstadoInterno(ingrediente, Parametros(), hoje).para_memoria()
    rastro = MotorDeInferencia(BaseDeConhecimento(regras)).executar(memoria)
    return memoria, rastro


def test_encadeia_ate_a_sugestao_final(fazer_ingrediente, hoje):
    memoria, rastro = rodar_motor(fazer_ingrediente(consumo_diario=5, prazo_entrega_dias=3, embalagem=25,
                                                    lotes=[(22, 120)]), hoje)
    assert [disparo.regra_id for disparo in rastro] == ["R4", "R6", "R9", "R10"]
    assert memoria["S2"] == 50


def test_cada_regra_dispara_no_maximo_uma_vez(fazer_ingrediente, hoje):
    _memoria, rastro = rodar_motor(fazer_ingrediente(consumo_diario=3, prazo_entrega_dias=1, embalagem=2,
                                                     perecivel=True, vida_util_dias=4,
                                                     lotes=[(7, 3), (2, -1)]), hoje)
    ids_das_regras_disparadas = [disparo.regra_id for disparo in rastro]
    assert len(ids_das_regras_disparadas) == len(set(ids_das_regras_disparadas))


def test_ordem_das_regras_nao_muda_o_resultado(fazer_ingrediente, hoje):
    ingrediente = fazer_ingrediente(consumo_diario=2, prazo_entrega_dias=2, embalagem=5, perecivel=True,
                                    vida_util_dias=10, lotes=[(4, 2), (2, 9)])
    memoria_de_referencia, _rastro = rodar_motor(ingrediente, hoje)
    for semente in range(20):
        regras_embaralhadas = list(REGRAS_REPOSICAO)
        random.Random(semente).shuffle(regras_embaralhadas)
        memoria_com_regras_embaralhadas, _rastro = rodar_motor(ingrediente, hoje, regras_embaralhadas)
        assert memoria_com_regras_embaralhadas.como_dict() == memoria_de_referencia.como_dict()


def test_regra_nova_sem_mudar_o_motor(fazer_ingrediente, hoje):
    """Demonstra a separação base × motor: acrescenta R13 sem tocar no motor."""
    regra_r13_pedir_cotacao = Regra("R13", 2, "Compra grande: pedir cotação", "S₂ > 40 → aviso cotação",
                                    ("S2",), lambda memoria: memoria["S2"] > 40,
                                    lambda memoria: {"aviso_cotacao": True})
    memoria, rastro = rodar_motor(fazer_ingrediente(consumo_diario=5, prazo_entrega_dias=3, embalagem=25,
                                                    lotes=[(22, 120)]), hoje,
                                  list(REGRAS_REPOSICAO) + [regra_r13_pedir_cotacao])
    assert memoria["aviso_cotacao"] is True
    assert rastro[-1].regra_id == "R13"


def test_memoria_nao_aceita_fato_repetido():
    memoria = MemoriaDeTrabalho()
    memoria.afirmar("s", "REPOR", "teste")
    with pytest.raises(FatoJaExisteErro):
        memoria.afirmar("s", "OK", "teste")


def test_base_recusa_ids_repetidos():
    with pytest.raises(ValueError):
        BaseDeConhecimento(list(REGRAS_REPOSICAO) + [REGRAS_REPOSICAO[0]])
"""Testes das regras isoladas.

Cada teste monta uma memória à mão, só com os fatos de que a regra precisa,
e confere se a regra dispara (ou não) e o que ela conclui.
"""
import itertools

import pytest

from agente.conhecimento.fatos import MemoriaDeTrabalho
from agente.conhecimento.regras_reposicao import (
    R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, REGRAS_REPOSICAO, arredondar_para_embalagem,
)
from agente.dominio.recomendacao import Situacao
from agente.estado.estado_interno import LoteNaMemoria


def criar_memoria(**fatos):
    memoria = MemoriaDeTrabalho()
    for nome_do_fato, valor_do_fato in fatos.items():
        memoria.afirmar(nome_do_fato, valor_do_fato, "teste")
    return memoria


@pytest.mark.parametrize("regra, fatos, situacao_esperada", [
    (R1, dict(c=0), Situacao.SEM_USO),
    (R2, dict(c=1, E=0), Situacao.EM_FALTA),
    (R3, dict(c=30, E=40, F=60), Situacao.CRITICO),
    (R4, dict(c=5, E=22, F=10, P=0, N=25), Situacao.REPOR),
    (R5, dict(c=4, E=30, F=8, P=0, N=16), Situacao.OK),
])
def test_grupo1_dispara(regra, fatos, situacao_esperada):
    memoria = criar_memoria(**fatos)
    assert regra.pode_disparar(memoria)
    assert regra.disparar(memoria) == {"s": situacao_esperada}


def test_regra_sem_premissas_nao_dispara():
    assert not R4.pode_disparar(criar_memoria(c=5, E=22))   # faltam F, P e N


def test_grupo1_exatamente_uma_regra_vale():
    """Para qualquer combinação de valores, só uma regra de R1 a R5 é verdadeira.

    F é sempre c × dias de folga, com dias de folga >= 1 (Parametros garante isso).
    """
    valores_de_teste = [0, 1, 5, 10, 25, 40]
    for consumo, estoque, a_caminho, dias_folga, ponto_de_pedido in itertools.product(
            valores_de_teste, valores_de_teste, valores_de_teste, [1, 2, 3], valores_de_teste):
        folga = consumo * dias_folga
        memoria = criar_memoria(c=consumo, E=estoque, P=a_caminho, F=folga, N=ponto_de_pedido)
        ids_das_regras_verdadeiras = [regra.id for regra in (R1, R2, R3, R4, R5)
                                      if regra.pode_disparar(memoria)]
        assert len(ids_das_regras_verdadeiras) == 1, (consumo, estoque, a_caminho, folga, ponto_de_pedido,
                                                      ids_das_regras_verdadeiras)


def test_R6_sugestao_inicial_e_Q():
    assert R6.disparar(criar_memoria(s=Situacao.REPOR, Q=38)) == {"S0": 38}
    assert not R6.pode_disparar(criar_memoria(s=Situacao.OK, Q=38))
    assert not R6.pode_disparar(criar_memoria(s=Situacao.CRITICO, Q=0))


def test_R7_aviso_quando_pedido_cobre():
    assert R7.pode_disparar(criar_memoria(s=Situacao.CRITICO, Q=-40))
    assert not R7.pode_disparar(criar_memoria(s=Situacao.REPOR, Q=-40))


def test_R8_limita_pela_vida_util():
    assert R8.disparar(criar_memoria(S0=23, perecivel=True, c=3, V=4)) == {"S1": 12}
    assert R8.disparar(criar_memoria(S0=16, perecivel=True, c=2, V=10)) == {"S1": 16}
    assert not R8.pode_disparar(criar_memoria(S0=16, perecivel=False, c=2, V=10))


def test_R9_nao_perecivel_copia():
    assert R9.disparar(criar_memoria(S0=38, perecivel=False)) == {"S1": 38}


@pytest.mark.parametrize("sugestao_s1, tamanho_embalagem, sugestao_s2_esperada",
                         [(38, 25, 50), (16, 5, 20), (62, 27, 81), (14, 1, 14), (50, 25, 50)])
def test_R10_arredonda_para_embalagem(sugestao_s1, tamanho_embalagem, sugestao_s2_esperada):
    assert R10.disparar(criar_memoria(S1=sugestao_s1, B=tamanho_embalagem)) == {"S2": sugestao_s2_esperada}


def test_arredondamento_tolera_ponto_flutuante():
    assert arredondar_para_embalagem(0.1 * 3, 0.1) == pytest.approx(0.3)


def test_R11_e_R12_validade():
    lotes_na_memoria = (LoteNaMemoria(1, 7, 3), LoteNaMemoria(2, 2, -1), LoteNaMemoria(3, 5, 10),
                        LoteNaMemoria(4, 1, 0))
    memoria = criar_memoria(lotes=lotes_na_memoria, A=3)
    assert R11.disparar(memoria) == {"lotes_usar_primeiro": (1,)}
    assert R12.disparar(memoria) == {"lotes_vencidos": (2, 4)}


def test_ids_unicos_e_doze_regras():
    assert len({regra.id for regra in REGRAS_REPOSICAO}) == 12
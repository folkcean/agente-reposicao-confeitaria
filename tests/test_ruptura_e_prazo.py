"""Testes do tempo até a ruptura (D) e do prazo-limite para o pedido (M).

Os ingredientes usam os valores padrão do fazer_ingrediente (consumo 5 por dia,
prazo de entrega 3 dias), então só os lotes, a embalagem e o a_caminho mudam.
"""
from agente.agente import AgenteReposicao
from agente.dominio.modelos import Ingrediente, Parametros
from agente.dominio.repositorio import RepositorioMemoria
from agente.estado.estado_interno import EstadoInterno


def test_dias_ate_a_ruptura_e_margem(fazer_ingrediente, hoje):
    farinha = fazer_ingrediente(lotes=[(22, 120)])
    memoria = EstadoInterno(farinha, Parametros(), hoje).para_memoria()
    assert memoria["D"] == 4.4          # 22 ÷ 5
    assert memoria["M"] == 1.4          # 4,4 − 3
    assert memoria.fato("D").dependencias == ("E", "c")
    assert memoria.fato("M").dependencias == ("D", "L")


def test_sem_consumo_nao_tem_ruptura(hoje):
    essencia = Ingrediente(id=1, nome="Essência", unidade="frasco", consumo_diario=0,
                           prazo_entrega_dias=7, embalagem=1, perecivel=False, vida_util_dias=None)
    memoria = EstadoInterno(essencia, Parametros(), hoje).para_memoria()
    assert "D" not in memoria and "M" not in memoria


def test_aviso_com_data_para_pedir(fazer_ingrediente, hoje):
    agente = AgenteReposicao(RepositorioMemoria([fazer_ingrediente(lotes=[(22, 120)], embalagem=25)]))
    recomendacao = agente.avaliar_ingrediente(1, hoje)
    assert recomendacao.sugestao_compra == 50
    assert recomendacao.avisos[0] == (
        "Acaba em 4,4 dia(s) no ritmo atual: peça até 21/11 para a entrega chegar antes."
    )


def test_aviso_quando_ja_nao_da_tempo(fazer_ingrediente, hoje):
    agente = AgenteReposicao(RepositorioMemoria([fazer_ingrediente(lotes=[(10, 200)])]))
    recomendacao = agente.avaliar_ingrediente(1, hoje)
    assert recomendacao.avisos[0] == (
        "Acaba em 2 dia(s) e a entrega leva 3 dia(s): "
        "deve faltar por cerca de 1 dia(s), mesmo pedindo hoje."
    )


def test_sem_compra_sem_aviso_de_prazo(fazer_ingrediente, hoje):
    agente = AgenteReposicao(RepositorioMemoria([fazer_ingrediente(lotes=[(40, 15)], a_caminho=300)]))
    recomendacao = agente.avaliar_ingrediente(1, hoje)
    assert recomendacao.sugestao_compra is None
    assert not any("peça" in aviso or "faltar" in aviso for aviso in recomendacao.avisos)
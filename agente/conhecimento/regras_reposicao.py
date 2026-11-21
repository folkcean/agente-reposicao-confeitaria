"""As 12 regras de negócio do agente:
    c  consumo por dia            E  estoque útil (lotes não vencidos)
    P  quantidade a caminho       L  prazo de entrega (dias)
    C  dias de cobertura          F  folga = c × dias de folga
    N  nível mínimo = c × L + F   Q  quanto comprar = c × (L + C) + F − (E + P)
    V  vida útil (dias)           B  tamanho da embalagem
    A  antecedência do aviso de validade
    s  situação                   S0, S1, S2  sugestão inicial, ajustada e final
    lotes  lista de lotes com dias para vencer

Grupo 1 (R1-R5): exatamente UMA regra é verdadeira para cada ingrediente.
Grupo 2 (R6-R10): calcula a sugestão de compra, em cadeia S0 → S1 → S2.
Grupo 3 (R11-R12): avisos de validade dos lotes.

Cada regra tem duas funções logo acima dela: a condição (o SE) e a
conclusão (o ENTÃO). As duas só são chamadas depois que o motor confere
que todas as premissas da regra existem na memória.
"""
from __future__ import annotations

import math

from agente.conhecimento.fatos import MemoriaDeTrabalho
from agente.conhecimento.regra import Regra
from agente.dominio.recomendacao import Situacao

PRECISAM_ATENCAO = (Situacao.EM_FALTA, Situacao.CRITICO, Situacao.REPOR)
PRATELEIRA_RUIM = (Situacao.EM_FALTA, Situacao.CRITICO)


def arredondar_para_embalagem(quantidade: float, embalagem: float) -> float:
    """⌈quantidade ÷ embalagem⌉ × embalagem, tolerando erros de ponto flutuante."""
    embalagens_inteiras = math.ceil(round(quantidade / embalagem, 6))
    return round(embalagens_inteiras * embalagem, 6)


def _lotes_a_vencer(memoria: MemoriaDeTrabalho) -> tuple[int, ...]:
    """Ids dos lotes que ainda não venceram, mas vencem em até A dias."""
    antecedencia_do_aviso = memoria["A"]
    ids_dos_lotes: list[int] = []
    for lote in memoria["lotes"]:
        ainda_nao_venceu = lote.dias_para_vencer > 0
        vence_dentro_do_aviso = lote.dias_para_vencer <= antecedencia_do_aviso
        if ainda_nao_venceu and vence_dentro_do_aviso:
            ids_dos_lotes.append(lote.id)
    return tuple(ids_dos_lotes)


def _lotes_vencidos(memoria: MemoriaDeTrabalho) -> tuple[int, ...]:
    """Ids dos lotes que já venceram (zero ou menos dias para vencer)."""
    ids_dos_lotes: list[int] = []
    for lote in memoria["lotes"]:
        if lote.dias_para_vencer <= 0:
            ids_dos_lotes.append(lote.id)
    return tuple(ids_dos_lotes)


# ---------------------------------------------------------------- Grupo 1: situação
def _condicao_r1(memoria: MemoriaDeTrabalho) -> bool:
    """c = 0"""
    consumo = memoria["c"]
    return consumo == 0


def _conclusao_r1(memoria: MemoriaDeTrabalho) -> dict:
    return {"s": Situacao.SEM_USO}


R1 = Regra(
    id="R1", grupo=1,
    descricao="O ingrediente não é consumido: SEM USO",
    formula="c = 0 → s = SEM USO",
    premissas=("c",),
    condicao=_condicao_r1,
    conclusao=_conclusao_r1,
)


def _condicao_r2(memoria: MemoriaDeTrabalho) -> bool:
    """c > 0 ∧ E = 0"""
    consumo = memoria["c"]
    estoque = memoria["E"]
    e_consumido = consumo > 0
    prateleira_vazia = estoque == 0
    return e_consumido and prateleira_vazia


def _conclusao_r2(memoria: MemoriaDeTrabalho) -> dict:
    return {"s": Situacao.EM_FALTA}


R2 = Regra(
    id="R2", grupo=1,
    descricao="É consumido, mas a prateleira está vazia: EM FALTA",
    formula="c > 0 ∧ E = 0 → s = EM FALTA",
    premissas=("c", "E"),
    condicao=_condicao_r2,
    conclusao=_conclusao_r2,
)


def _condicao_r3(memoria: MemoriaDeTrabalho) -> bool:
    """c > 0 ∧ 0 < E < F"""
    consumo = memoria["c"]
    estoque = memoria["E"]
    folga = memoria["F"]
    e_consumido = consumo > 0
    tem_estoque = estoque > 0
    abaixo_da_folga = estoque < folga
    return e_consumido and tem_estoque and abaixo_da_folga


def _conclusao_r3(memoria: MemoriaDeTrabalho) -> dict:
    return {"s": Situacao.CRITICO}


R3 = Regra(
    id="R3", grupo=1,
    descricao="Há estoque, mas menos que a folga: CRÍTICO",
    formula="c > 0 ∧ 0 < E < F → s = CRÍTICO",
    premissas=("c", "E", "F"),
    condicao=_condicao_r3,
    conclusao=_conclusao_r3,
)


def _condicao_r4(memoria: MemoriaDeTrabalho) -> bool:
    """c > 0 ∧ E ≥ F ∧ (E + P) ≤ N"""
    consumo = memoria["c"]
    estoque = memoria["E"]
    folga = memoria["F"]
    a_caminho = memoria["P"]
    nivel_minimo = memoria["N"]
    e_consumido = consumo > 0
    folga_intacta = estoque >= folga
    nao_passa_do_nivel_minimo = (estoque + a_caminho) <= nivel_minimo
    return e_consumido and folga_intacta and nao_passa_do_nivel_minimo


def _conclusao_r4(memoria: MemoriaDeTrabalho) -> dict:
    return {"s": Situacao.REPOR}


R4 = Regra(
    id="R4", grupo=1,
    descricao="Folga intacta, mas estoque + a caminho não passa do nível mínimo: REPOR",
    formula="c > 0 ∧ E ≥ F ∧ (E + P) ≤ N → s = REPOR",
    premissas=("c", "E", "F", "P", "N"),
    condicao=_condicao_r4,
    conclusao=_conclusao_r4,
)


def _condicao_r5(memoria: MemoriaDeTrabalho) -> bool:
    """c > 0 ∧ E ≥ F ∧ (E + P) > N"""
    consumo = memoria["c"]
    estoque = memoria["E"]
    folga = memoria["F"]
    a_caminho = memoria["P"]
    nivel_minimo = memoria["N"]
    e_consumido = consumo > 0
    folga_intacta = estoque >= folga
    passa_do_nivel_minimo = (estoque + a_caminho) > nivel_minimo
    return e_consumido and folga_intacta and passa_do_nivel_minimo


def _conclusao_r5(memoria: MemoriaDeTrabalho) -> dict:
    return {"s": Situacao.OK}


R5 = Regra(
    id="R5", grupo=1,
    descricao="Folga intacta e estoque + a caminho passa do nível mínimo: OK",
    formula="c > 0 ∧ E ≥ F ∧ (E + P) > N → s = OK",
    premissas=("c", "E", "F", "P", "N"),
    condicao=_condicao_r5,
    conclusao=_conclusao_r5,
)


# ---------------------------------------------------------------- Grupo 2: quanto sugerir
def _condicao_r6(memoria: MemoriaDeTrabalho) -> bool:
    """s ∈ {EM FALTA, CRÍTICO, REPOR} ∧ Q > 0"""
    situacao = memoria["s"]
    quanto_comprar = memoria["Q"]
    precisa_de_atencao = situacao in PRECISAM_ATENCAO
    falta_material = quanto_comprar > 0
    return precisa_de_atencao and falta_material


def _conclusao_r6(memoria: MemoriaDeTrabalho) -> dict:
    quanto_comprar = memoria["Q"]
    return {"S0": quanto_comprar}


R6 = Regra(
    id="R6", grupo=2,
    descricao="Precisa de atenção e falta material: a sugestão inicial é Q",
    formula="s ∈ {EM FALTA, CRÍTICO, REPOR} ∧ Q > 0 → S₀ = Q",
    premissas=("s", "Q"),
    condicao=_condicao_r6,
    conclusao=_conclusao_r6,
)


def _condicao_r7(memoria: MemoriaDeTrabalho) -> bool:
    """s ∈ {EM FALTA, CRÍTICO} ∧ Q ≤ 0"""
    situacao = memoria["s"]
    quanto_comprar = memoria["Q"]
    prateleira_ruim = situacao in PRATELEIRA_RUIM
    pedido_ja_cobre = quanto_comprar <= 0
    return prateleira_ruim and pedido_ja_cobre


def _conclusao_r7(memoria: MemoriaDeTrabalho) -> dict:
    return {"aviso_pedido_a_caminho": True}


R7 = Regra(
    id="R7", grupo=2,
    descricao="A prateleira está mal, mas o pedido a caminho já cobre tudo: avisar",
    formula="s ∈ {EM FALTA, CRÍTICO} ∧ Q ≤ 0 → aviso",
    premissas=("s", "Q"),
    condicao=_condicao_r7,
    conclusao=_conclusao_r7,
)


def _condicao_r8(memoria: MemoriaDeTrabalho) -> bool:
    """perecível (o valor tem que ser exatamente True)"""
    return memoria["perecivel"] is True


def _conclusao_r8(memoria: MemoriaDeTrabalho) -> dict:
    """S₁ = mín(S₀, c × V): não compra mais do que se usa antes de estragar."""
    sugestao_inicial = memoria["S0"]
    uso_durante_a_vida_util = memoria["c"] * memoria["V"]
    sugestao_ajustada = min(sugestao_inicial, uso_durante_a_vida_util)
    return {"S1": round(sugestao_ajustada, 6)}


R8 = Regra(
    id="R8", grupo=2,
    descricao="Perecível: não comprar mais do que se usa antes de estragar",
    formula="S₀ existe ∧ perecível → S₁ = mín(S₀, c × V)",
    premissas=("S0", "perecivel", "c", "V"),
    condicao=_condicao_r8,
    conclusao=_conclusao_r8,
)


def _condicao_r9(memoria: MemoriaDeTrabalho) -> bool:
    """não perecível (o valor tem que ser exatamente False)"""
    return memoria["perecivel"] is False


def _conclusao_r9(memoria: MemoriaDeTrabalho) -> dict:
    sugestao_inicial = memoria["S0"]
    return {"S1": sugestao_inicial}


R9 = Regra(
    id="R9", grupo=2,
    descricao="Não perecível: a sugestão ajustada é igual à inicial",
    formula="S₀ existe ∧ não perecível → S₁ = S₀",
    premissas=("S0", "perecivel"),
    condicao=_condicao_r9,
    conclusao=_conclusao_r9,
)


def _condicao_r10(memoria: MemoriaDeTrabalho) -> bool:
    """Sempre verdadeira: basta S₁ e B existirem (as premissas)."""
    return True


def _conclusao_r10(memoria: MemoriaDeTrabalho) -> dict:
    sugestao_ajustada = memoria["S1"]
    embalagem = memoria["B"]
    sugestao_final = arredondar_para_embalagem(sugestao_ajustada, embalagem)
    return {"S2": sugestao_final}


R10 = Regra(
    id="R10", grupo=2,
    descricao="Arredondar a sugestão para embalagens inteiras",
    formula="S₁ existe → S₂ = ⌈S₁ ÷ B⌉ × B",
    premissas=("S1", "B"),
    condicao=_condicao_r10,
    conclusao=_conclusao_r10,
)


# ---------------------------------------------------------------- Grupo 3: validade
def _condicao_r11(memoria: MemoriaDeTrabalho) -> bool:
    """Existe pelo menos um lote com 0 < dₗ ≤ A."""
    return len(_lotes_a_vencer(memoria)) > 0


def _conclusao_r11(memoria: MemoriaDeTrabalho) -> dict:
    return {"lotes_usar_primeiro": _lotes_a_vencer(memoria)}


R11 = Regra(
    id="R11", grupo=3,
    descricao="Lote ainda bom, mas vence em até A dias: usar primeiro",
    formula="0 < dₗ ≤ A → aviso (usar primeiro)",
    premissas=("lotes", "A"),
    condicao=_condicao_r11,
    conclusao=_conclusao_r11,
)


def _condicao_r12(memoria: MemoriaDeTrabalho) -> bool:
    """Existe pelo menos um lote com dₗ ≤ 0."""
    return len(_lotes_vencidos(memoria)) > 0


def _conclusao_r12(memoria: MemoriaDeTrabalho) -> dict:
    return {"lotes_vencidos": _lotes_vencidos(memoria)}


R12 = Regra(
    id="R12", grupo=3,
    descricao="Lote já venceu: descartar",
    formula="dₗ ≤ 0 → aviso (descartar)",
    premissas=("lotes",),
    condicao=_condicao_r12,
    conclusao=_conclusao_r12,
)

REGRAS_REPOSICAO: tuple[Regra, ...] = (R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12)

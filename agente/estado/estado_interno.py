"""Estado interno: transforma a percepção de um ingrediente em fatos.

Recebe um Ingrediente (dados do banco), os Parametros e a data de hoje, e:

1. calcula E (estoque útil): soma dos lotes que ainda não venceram;
2. calcula as três contas da seção 6.2 da Fase 2:
       F = c × dias de folga                     (folga)
       N = c × L + F                             (nível mínimo)
       Q = c × (L + C) + F − (E + P)             (quanto comprar)
3. estima o que o banco não mostra diretamente (só quando c > 0):
       D = E ÷ c(dias até a ruptura, só a prateleira)
       M = D − L(margem para pedir; negativa = vai faltar)
4. grava tudo na memória de trabalho.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agente.conhecimento.fatos import MemoriaDeTrabalho
from agente.dominio.modelos import Ingrediente, Parametros

CASAS = 6  # arredondamento para evitar lixo de ponto flutuante (0.30000000000000004)

def _r(valor: float) -> float:
    return round(valor, CASAS)


@dataclass(frozen=True)
class LoteNaMemoria:
    """Um lote como o agente o enxerga: quantidade e dias até vencer."""

    id: int
    quantidade: float
    dias_para_vencer: int

    @property
    def vencido(self) -> bool:
        return self.dias_para_vencer <= 0


class EstadoInterno:
    """Modelo do mundo para UM ingrediente em UMA data."""

    def __init__(self, ingrediente: Ingrediente, parametros: Parametros, hoje: date) -> None:
        self.ingrediente = ingrediente
        self.parametros = parametros
        self.hoje = hoje

        lotes_na_memoria: list[LoteNaMemoria] = []
        for lote in ingrediente.lotes:
            dias_para_vencer = lote.dias_para_vencer(hoje)
            lotes_na_memoria.append(LoteNaMemoria(lote.id, lote.quantidade, dias_para_vencer))
        self.lotes = tuple(lotes_na_memoria)

        estoque_util = 0
        for lote in self.lotes:
            if not lote.vencido:
                estoque_util += lote.quantidade

        c = ingrediente.consumo_diario
        self.c = c
        self.L = ingrediente.prazo_entrega_dias
        self.P = ingrediente.a_caminho
        self.C = parametros.dias_cobertura
        self.E = _r(estoque_util)
        self.F = _r(c * parametros.dias_folga)
        self.N = _r(c * self.L + self.F)
        self.Q = _r(c * (self.L + self.C) + self.F - (self.E + self.P))

        if c > 0:
            self.D = _r(self.E / c)
            self.M = _r(self.D - self.L)
        else:
            self.D = None
            self.M = None



    def para_memoria(self) -> MemoriaDeTrabalho:
        """Cria a memória de trabalho com todos os fatos iniciais."""
        ingrediente = self.ingrediente
        parametros = self.parametros
        memoria = MemoriaDeTrabalho()

        # Percepções (sensores)
        memoria.afirmar("c", self.c, "sensor: consumo médio diário")
        memoria.afirmar("L", self.L, "sensor: prazo de entrega do fornecedor")
        memoria.afirmar("P", self.P, "sensor: pedidos ainda não entregues")
        memoria.afirmar("B", ingrediente.embalagem, "sensor: tamanho da embalagem")
        memoria.afirmar("perecivel", ingrediente.perecivel, "sensor: cadastro do ingrediente")
        if ingrediente.vida_util_dias is not None:
            memoria.afirmar("V", ingrediente.vida_util_dias, "sensor: vida útil")
        memoria.afirmar("lotes", self.lotes, "sensor: lotes em estoque")

        # Parâmetros
        memoria.afirmar("C", self.C, "parâmetro: dias de cobertura")
        memoria.afirmar("A", parametros.aviso_validade_dias, "parâmetro: aviso de validade")

        # Cálculos do estado interno
        memoria.afirmar("E", self.E, "cálculo: E = soma dos lotes não vencidos", ("lotes",))
        memoria.afirmar(
            "F", self.F,
            f"cálculo: F = c × dias de folga = {self.c:g} × {parametros.dias_folga}", ("c",),
        )
        memoria.afirmar(
            "N", self.N,
            f"cálculo: N = c × L + F = {self.c:g} × {self.L} + {self.F:g}", ("c", "L", "F"),
        )
        memoria.afirmar(
            "Q", self.Q,
            f"cálculo: Q = c × (L + C) + F − (E + P) = "
            f"{self.c:g} × ({self.L} + {self.C}) + {self.F:g} − ({self.E:g} + {self.P:g})",
            ("c", "L", "C", "F", "E", "P"),
        )
        if self.D is not None:
            memoria.afirmar(
                "D", self.D,
                f"cálculo: D = E ÷ c = {self.E:g} ÷ {self.c:g}", ("E", "c"),
            )
            memoria.afirmar(
                "M", self.M,
                f"cálculo: M = D − L = {self.D:g} − {self.L}", ("D", "L"),
            )
        return memoria

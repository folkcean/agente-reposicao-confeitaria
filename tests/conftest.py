"""Configuração compartilhada dos testes (Tarefa 0, feita em dupla).

Fixtures:
- hoje:               data fixa (2026-11-20) para os testes serem reproduzíveis.
- fazer_ingrediente:  fábrica de Ingrediente com valores padrão.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from agente.dominio.modelos import Ingrediente, Lote

HOJE = date(2026, 11, 20)


@pytest.fixture
def hoje() -> date:
    return HOJE


@pytest.fixture
def fazer_ingrediente():
    def criar_ingrediente_com_padroes(
        nome: str = "Teste",
        consumo_diario: float = 5,
        prazo_entrega_dias: int = 3,
        embalagem: float = 1,
        perecivel: bool = False,
        vida_util_dias: int | None = None,
        a_caminho: float = 0,
        lotes: list[tuple[float, int]] = (),
        id_ingrediente: int = 1,
        unidade: str = "kg",
    ) -> Ingrediente:
        return Ingrediente(
            id=id_ingrediente, nome=nome, unidade=unidade, consumo_diario=consumo_diario,
            prazo_entrega_dias=prazo_entrega_dias, embalagem=embalagem, perecivel=perecivel,
            vida_util_dias=vida_util_dias, a_caminho=a_caminho,
            lotes=tuple(Lote(id_ingrediente * 100 + indice_do_lote, quantidade,
                             HOJE + timedelta(days=dias_para_vencer))
                        for indice_do_lote, (quantidade, dias_para_vencer) in enumerate(lotes)),
        )
    return criar_ingrediente_com_padroes
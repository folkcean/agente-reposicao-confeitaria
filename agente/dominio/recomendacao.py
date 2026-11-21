"""Modelos de SAÍDA do agente: o que ele entrega para a interface.

- Situacao:     as cinco situações possíveis de um ingrediente (grupo 1 de regras),
                com uma prioridade para ordenar a lista na tela.
- Recomendacao: O texto final.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Situacao(str, Enum):
    """Situação de um ingrediente, decidida pelas regras R1 a R5."""

    EM_FALTA = "EM FALTA"
    CRITICO = "CRÍTICO"
    REPOR = "REPOR"
    OK = "OK"
    SEM_USO = "SEM USO"

    @property
    def prioridade(self) -> int:
        """Menor número = mais urgente. Usado para ordenar a lista."""
        ordem = [Situacao.EM_FALTA, Situacao.CRITICO, Situacao.REPOR, Situacao.OK, Situacao.SEM_USO]
        return ordem.index(self)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Recomendacao:
    """Resultado da avaliação de um ingrediente.

    Atributos:
        ingrediente_id, ingrediente, unidade: identificação.
        situacao: uma das cinco situações (R1 a R5).
        sugestao_compra: quantidade final sugerida (S₂), já arredondada para
            embalagens inteiras; None quando não há sugestão.
        avisos: mensagens para o usuário (R7, R11, R12).
        regras_disparadas: ids das regras na ordem em que dispararam.
    """

    ingrediente_id: int
    ingrediente: str
    unidade: str
    situacao: Situacao
    sugestao_compra: float | None
    avisos: tuple[str, ...]
    regras_disparadas: tuple[str, ...]

    @property
    def precisa_comprar(self) -> bool:
        return self.sugestao_compra is not None and self.sugestao_compra > 0

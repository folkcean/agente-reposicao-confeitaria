"""Base de conhecimento: o conjunto de regras do sistema especialista.

A base guarda o conhecimento GERAL e permanente (as regras R1 a R12).
O conhecimento ESPECÍFICO, sobre o ingrediente avaliado no momento, fica na
memória de trabalho (fatos.py), que é criada de novo a cada avaliação.
"""
from __future__ import annotations

from collections.abc import Iterable

from agente.conhecimento.regra import Regra


class BaseDeConhecimento:
    """Coleção ordenada de regras, com ids únicos."""

    def __init__(self, regras: Iterable[Regra]) -> None:
        self._regras: list[Regra] = []
        for regra in regras:
            self.adicionar(regra)

    @classmethod
    def padrao(cls) -> "BaseDeConhecimento":
        """A base com as 12 regras de reposição do projeto."""
        from agente.conhecimento.regras_reposicao import REGRAS_REPOSICAO

        return cls(REGRAS_REPOSICAO)

    def adicionar(self, regra: Regra) -> None:
        """Acrescenta uma regra no fim da base. Recusa id repetido."""
        for regra_existente in self._regras:
            if regra_existente.id == regra.id:
                raise ValueError(f"Já existe uma regra com id {regra.id}")
        self._regras.append(regra)

    def remover(self, regra_id: str) -> None:
        """Tira da base a regra com esse id (se não existir, não faz nada)."""
        regras_que_ficam: list[Regra] = []
        for regra in self._regras:
            if regra.id != regra_id:
                regras_que_ficam.append(regra)
        self._regras = regras_que_ficam

    def regra(self, regra_id: str) -> Regra:
        """A regra com esse id. KeyError se não existir."""
        for candidata in self._regras:
            if candidata.id == regra_id:
                return candidata
        raise KeyError(regra_id)

    @property
    def regras(self) -> tuple[Regra, ...]:
        return tuple(self._regras)

    def por_grupo(self, grupo: int) -> tuple[Regra, ...]:
        """As regras de um grupo (1, 2 ou 3), na ordem da base."""
        regras_do_grupo: list[Regra] = []
        for regra in self._regras:
            if regra.grupo == grupo:
                regras_do_grupo.append(regra)
        return tuple(regras_do_grupo)

    def __len__(self) -> int:
        return len(self._regras)

    def __iter__(self):
        return iter(self._regras)

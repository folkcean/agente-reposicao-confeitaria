"""Interface (porta) entre o agente e a fonte de dados.

O agente nunca acessa o banco diretamente: ele pede os ingredientes a um
RepositorioEstoque.
- RepositorioMemoria (aqui):             lista em memória, usada nos testes.
- RepositorioSQLite (dados/):            banco SQLite de demonstração.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import date

from agente.dominio.modelos import Ingrediente


class RepositorioEstoque(ABC):
    """Contrato que toda fonte de dados do agente precisa cumprir."""

    @abstractmethod
    def listar_ingredientes(self, hoje: date) -> list[Ingrediente]:
        """Devolve todos os ingredientes cadastrados, com dados atualizados até `hoje`."""

    @abstractmethod
    def buscar_ingrediente(self, ingrediente_id: int, hoje: date) -> Ingrediente | None:
        """Devolve um ingrediente pelo id, ou None se não existir."""


class RepositorioMemoria(RepositorioEstoque):
    """Repositório que guarda ingredientes numa lista. Ideal para testes."""

    def __init__(self, ingredientes: Iterable[Ingrediente] = ()) -> None:
        self._ingredientes: dict[int, Ingrediente] = {i.id: i for i in ingredientes}

    def adicionar(self, ingrediente: Ingrediente) -> None:
        self._ingredientes[ingrediente.id] = ingrediente

    def listar_ingredientes(self, hoje: date) -> list[Ingrediente]:
        return list(self._ingredientes.values())

    def buscar_ingrediente(self, ingrediente_id: int, hoje: date) -> Ingrediente | None:
        return self._ingredientes.get(ingrediente_id)

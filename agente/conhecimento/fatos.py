"""Fatos e memória de trabalho.

Um FATO é uma afirmação sobre o ingrediente avaliado, por exemplo
"consumo por dia (c) = 5" ou "situação (s) = REPOR". Cada fato guarda:

- origem:       de onde veio ("sensor", "parâmetro", "cálculo: ..." ou "regra R4");
- dependencias: de quais outros fatos ele foi derivado.

A MEMÓRIA DE TRABALHO é o conjunto de fatos sobre UM ingrediente durante
uma avaliação (o termo vem dos sistemas de produção; Russell e Norvig,
cap. 9). Ela é monotônica: um fato afirmado nunca é apagado nem alterado.
Tentar afirmar de novo o mesmo fato gera FatoJaExisteErro, o que denuncia
duas regras concluindo a mesma coisa (erro de modelagem da base).

As dependências permitem explicar qualquer conclusão percorrendo o caminho
de volta até os dados do banco (encadeamento para trás, explicador.py).
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

class FatoJaExisteErro(Exception):
    """Lançada quando se tenta afirmar um fato que já está na memória."""


@dataclass(frozen=True)
class Fato:
    """Uma afirmação sobre o ingrediente avaliado."""
    nome: str
    valor: Any
    origem: str
    dependencias: tuple[str, ...] = ()


class MemoriaDeTrabalho:
    """Conjunto de fatos sobre um ingrediente. Só aceita fatos novos."""

    def __init__(self) -> None:
        self._fatos: dict[str, Fato] = {}

    def afirmar(self, nome: str, valor: Any, origem: str, dependencias: tuple[str, ...] = ()) -> Fato:
        """Acrescenta um fato novo (operação TELL de Russell e Norvig)."""
        if nome in self._fatos:
            raise FatoJaExisteErro(
                f"O fato '{nome}' já existe (valor {self._fatos[nome].valor!r}); "
                f"nenhuma regra pode alterá-lo."
            )
        fato = Fato(nome, valor, origem, tuple(dependencias))
        self._fatos[nome] = fato
        return fato

    def __contains__(self, nome: object) -> bool:
        return nome in self._fatos

    def __getitem__(self, nome: str) -> Any:
        """Valor de um fato: memoria["c"]. KeyError se não existir."""
        return self._fatos[nome].valor

    def fato(self, nome: str) -> Fato:
        """O objeto Fato completo (com origem e dependências)."""
        return self._fatos[nome]

    def get(self, nome: str, padrao: Any = None) -> Any:
        fato = self._fatos.get(nome)
        return padrao if fato is None else fato.valor

    def __iter__(self) -> Iterator[Fato]:
        return iter(self._fatos.values())

    def __len__(self) -> int:
        return len(self._fatos)

    def como_dict(self) -> dict[str, Any]:
        """Todos os fatos como {nome: valor}. Útil para testes e depuração."""
        return {nome: fato.valor for nome, fato in self._fatos.items()}
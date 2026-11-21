"""A classe Regra: uma regra de produção SE/ENTÃO.

- premissas: nomes dos fatos que precisam EXISTIR na memória para ela ser
             avaliada (é assim que o encadeamento sabe a ordem natural);
- condicao:  função que recebe a memória e responde True/False (o SE);
- conclusao: função que recebe a memória e devolve os fatos novos (o ENTÃO),
             como dicionário {nome_do_fato: valor}.

A regra não altera a memória sozinha: quem afirma os fatos novos é o motor.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agente.conhecimento.fatos import MemoriaDeTrabalho

Condicao = Callable[[MemoriaDeTrabalho], bool]
Conclusao = Callable[[MemoriaDeTrabalho], dict[str, Any]]


@dataclass(frozen=True)
class Regra:
    """Regra SE/ENTÃO da base de conhecimento."""

    id: str
    grupo: int
    descricao: str
    formula: str
    premissas: tuple[str, ...]
    condicao: Condicao
    conclusao: Conclusao

    def premissas_satisfeitas(self, memoria: MemoriaDeTrabalho) -> bool:
        """Todos os fatos de que a regra precisa já existem?"""
        for nome_do_fato in self.premissas:
            if nome_do_fato not in memoria:
                return False
        return True

    def pode_disparar(self, memoria: MemoriaDeTrabalho) -> bool:
        """Premissas existem E a condição (SE) é verdadeira."""
        if not self.premissas_satisfeitas(memoria):
            return False
        condicao_verdadeira = bool(self.condicao(memoria))
        return condicao_verdadeira

    def disparar(self, memoria: MemoriaDeTrabalho) -> dict[str, Any]:
        """Calcula a conclusão (ENTÃO). Não grava nada: devolve os fatos novos."""
        fatos_novos = self.conclusao(memoria)
        return dict(fatos_novos)

    def __str__(self) -> str:
        return f"{self.id}: {self.formula}"

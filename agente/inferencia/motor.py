"""Motor de inferência por encadeamento para frente.

Ciclo (reconhecer-agir dos sistemas de produção):

1. MATCH:  monta a agenda com as regras que ainda não dispararam e cujas
           premissas existem e cuja condição é verdadeira;
2. SELECT: se a agenda estiver vazia, para (ponto fixo); senão escolhe a
           primeira regra da agenda (ordem de cadastro na base);
3. ACT:    afirma na memória os fatos que a regra concluiu, anota o disparo
           no rastro e volta ao passo 1.

Propriedades garantidas:
- cada regra dispara no máximo uma vez por avaliação (refração), então o
  motor sempre termina em no máximo len(base) ciclos;
- como a memória só aceita fatos novos e as regras foram escritas para não
  concluir o mesmo fato, a ORDEM das regras não muda o resultado final
  (há um teste que embaralha as regras para provar isso).

O motor não conhece nenhuma regra específica: ele só pergunta a cada Regra
"pode disparar?" e "o que você conclui?".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agente.conhecimento.base import BaseDeConhecimento
from agente.conhecimento.fatos import MemoriaDeTrabalho


@dataclass(frozen=True)
class Disparo:
    """Registro de uma regra que disparou (uma linha do rastro)."""

    ordem: int
    regra_id: str
    premissas: dict[str, Any]
    conclusoes: dict[str, Any]


class MotorDeInferencia:
    """Aplica as regras de uma base sobre uma memória de trabalho."""

    def __init__(self, base: BaseDeConhecimento) -> None:
        self.base = base

    def agenda(self, memoria: MemoriaDeTrabalho, ja_disparadas: set[str]) -> list:
        """Regras prontas para disparar neste ciclo (fase MATCH)."""
        regras_prontas = []
        for regra in self.base.regras:
            if regra.id in ja_disparadas:
                continue                      # refração: cada regra dispara uma vez só
            if regra.pode_disparar(memoria):
                regras_prontas.append(regra)
        return regras_prontas

    def executar(self, memoria: MemoriaDeTrabalho) -> list[Disparo]:
        """Encadeia para frente até o ponto fixo. Devolve o rastro de disparos."""
        ja_disparadas: set[str] = set()
        rastro: list[Disparo] = []
        while True:
            # MATCH
            agenda = self.agenda(memoria, ja_disparadas)
            if len(agenda) == 0:
                break                         # ponto fixo: nenhuma regra nova pode disparar

            # SELECT
            regra = agenda[0]

            # ACT
            conclusoes = regra.disparar(memoria)
            for nome, valor in conclusoes.items():
                memoria.afirmar(nome, valor, f"regra {regra.id}", regra.premissas)
            ja_disparadas.add(regra.id)

            valores_das_premissas: dict[str, Any] = {}
            for nome_da_premissa in regra.premissas:
                valores_das_premissas[nome_da_premissa] = memoria[nome_da_premissa]

            disparo = Disparo(
                ordem=len(rastro) + 1,
                regra_id=regra.id,
                premissas=valores_das_premissas,
                conclusoes=conclusoes,
            )
            rastro.append(disparo)
        return rastro

"""Base de conhecimento do sistema especialista .

- fatos.py:            Fato e MemoriaDeTrabalho (os fatos sobre um ingrediente).
- regra.py:            a classe Regra (uma regra SE/ENTÃO).
- regras_reposicao.py: as 12 regras de negócio (R1 a R12).
- base.py:             BaseDeConhecimento, que guarda e organiza as regras.

Nada aqui sabe COMO as regras são aplicadas: isso é papel do motor
(agente/inferencia/motor.py).
"""
from agente.conhecimento.base import BaseDeConhecimento
from agente.conhecimento.fatos import Fato, FatoJaExisteErro, MemoriaDeTrabalho
from agente.conhecimento.regra import Regra

__all__ = ["BaseDeConhecimento", "Fato", "FatoJaExisteErro", "MemoriaDeTrabalho", "Regra"]

"""Motor de inferência e explicador.

- motor.py:      encadeamento para frente (forward chaining).
- explicador.py: encadeamento para trás sobre as dependências dos fatos,
                 para responder "por que o agente sugeriu isso?".
"""
from agente.inferencia.explicador import Explicador
from agente.inferencia.motor import Disparo, MotorDeInferencia

__all__ = ["Disparo", "Explicador", "MotorDeInferencia"]

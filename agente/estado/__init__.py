"""Estado interno do agente: o modelo do mundo.

É o que faz o agente ser "baseado em modelo":
ele não reage só ao estoque na prateleira, mas também ao que não vê
diretamente, como o pedido que já está a caminho (P).
"""
from agente.estado.estado_interno import EstadoInterno, LoteNaMemoria

__all__ = ["EstadoInterno", "LoteNaMemoria"]

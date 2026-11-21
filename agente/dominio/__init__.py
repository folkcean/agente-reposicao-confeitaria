"""Contrato de dados do agente"""
from agente.dominio.modelos import Ingrediente, Lote, Parametros
from agente.dominio.recomendacao import Recomendacao, Situacao
from agente.dominio.repositorio import RepositorioEstoque, RepositorioMemoria

__all__ = [
    "Ingrediente", "Lote", "Parametros",
    "Recomendacao", "Situacao",
    "RepositorioEstoque", "RepositorioMemoria",
]

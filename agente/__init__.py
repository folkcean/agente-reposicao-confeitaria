"""Pacote do agente inteligente de reposição de estoque.

Agente Reativo Baseado em Modelo, implementado como Sistema Especialista.

- dominio/      contrato de dados (o que entra e o que sai do agente)
- estado/       estado interno: o modelo do mundo de cada ingrediente
- conhecimento/ base de conhecimento: fatos e regras SE/ENTÃO
- inferencia/   motor de inferência (encadeamento para frente) e explicador
- agente.py     o agente completo, que liga todas as partes
"""

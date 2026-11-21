#!/usr/bin/env bash
# Demonstração completa do agente, na ordem da apresentação.
# Uso: bash demo.sh
set -e
HOJE=2026-11-20
echo "== 1. Povoando o banco de exemplo (confeitaria.db)"
python main.py povoar --hoje $HOJE
echo; echo "== 2. Avaliando o estoque"
python main.py avaliar --hoje $HOJE
echo; echo "== 3. Explicando uma decisão (encadeamento para trás)"
python main.py explicar morango --hoje $HOJE
echo; echo "== 4. Experimentos de desempenho (5 repetições)"
python -m experimentos.simulacao --rep 5
echo; echo "== 5. Testes automatizados"
python -m pytest -q
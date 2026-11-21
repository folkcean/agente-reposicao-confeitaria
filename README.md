# Agente de Reposicao de Estoque - Confeitaria

Agente inteligente que sugere, para cada ingrediente, se está na hora de comprar e quanto comprar.
É um Agente Reativo Baseado em Modelo implementado como Sistema Especialista
(Russell e Norvig): estado interno + base de conhecimento com 12 regras SE/ENTÃO +
motor de inferência por encadeamento para frente.

Projeto academico da disciplina de inteligencia artificial - Anna Cecilia e Iarlo Henrique D. P. Pascoal

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py povoar --hoje 2026-11-20 # cria o banco com 10 ingredientes de exemplo
python main.py avaliar --hoje 2026-11-20 # roda o agente
python main.py explicar morango --hoje 2026-11-20 # mostra o porquê da decisão
python main.py regras # lista a base de conhecimento
pytest # roda todos os testes
```

## Estrutura

| Pasta | O que tem | 
|---|---|
| agente/dominio/ | Contrato de dados (entrada e saída do agente) |
| agente/estado/ | Estado interno: folga, nível mínimo, quanto comprar, dias até a ruptura| 
| agente/conhecimento/ | Fatos, regras R1–R12 e base de conhecimento |
| agente/inferencia/ | Motor (encadeamento para frente) e explicador|
| agente/agente.py | O agente completo |
| dados/ | Banco SQLite, sensores, cenários de exemplo |
| interface/, main.py | Saída no terminal e linha de comando |
| tests/ | Testes automatizados (pytest) |

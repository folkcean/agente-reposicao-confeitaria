# Agente de Reposicao de Estoque - Confeitaria

Agente inteligente que sugere, para cada ingrediente, se está na hora de comprar e quanto comprar.
É um Agente Reativo Baseado em Modelo implementado como Sistema Especialista
(Russell e Norvig): estado interno + base de conhecimento com 12 regras SE/ENTÃO +
motor de inferência por encadeamento para frente.

Projeto academico da disciplina de inteligencia artificial - Anna Cecilia e Iarlo Henrique D. P. Pascoal

## Instalação

```bash
git clone https://github.com/folkcean/agente-reposicao-confeitaria.git
cd agente-reposicao-confeitaria
python3 -m venv .venv
source .venv/bin/activate          
pip install -r requirements.txt
```

## Como executar

```bash
python main.py povoar   --hoje AAA-MM-DD   # cria confeitaria.db com 10 ingredientes de exemplo
python main.py avaliar  --hoje AAA-MM-DD   # roda o agente e mostra a lista de compras
python main.py explicar morango --AAA-MM-DD   # mostra o porquê de uma decisão
python main.py regras                        # lista a base de conhecimento (R1 a R12)
```

Use `--hoje 2026-11-20` para reproduzir exatamente os resultados do relatório.
Para ver tudo de uma vez, na ordem da apresentação: `bash demo.sh`.

## Testes e experimentos

```bash
python -m pytest                              # 78 testes automatizados
python -m experimentos.simulacao              # 90 dias simulados × 3 cenários × 30 repetições
python -m experimentos.simulacao --sensibilidade   # efeito dos dias de folga
```

Os testes cobrem as 12 regras, o motor (inclusive "a ordem das regras não muda o resultado" e
"regra nova sem mudar o motor"), o estado interno, o banco, a interface e os 10 cenários de
exemplo, cujo gabarito está em `dados/cenarios.py`. A saída dos experimentos usada no relatório
está em `experimentos/resultados.txt`.

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

"""Os dados de exemplo que povoam o agente.

Para que serve
--------------
O agente só mostra que funciona se houver dados para ele analisar. Este arquivo
descreve uma confeitaria de mentira com 10 ingredientes, 4 produtos e as vendas
dos últimos 28 dias. Os casos foram escolhidos para que CADA uma das 12 regras
(R1 a R12) dispare em pelo menos um ingrediente, e para aparecer cada situação:
EM FALTA, CRÍTICO, REPOR, OK e SEM USO.

Como foi feito
--------------
São só listas de tuplas, sem nenhuma lógica. Quem grava no banco é o povoar.py.

As vendas são CONSTANTES (a mesma quantidade todo dia). Assim o consumo médio
de cada ingrediente dá um número redondo, fácil de conferir à mão:

    Bolo de chocolate  10/dia  → farinha 3, açúcar 2, ovos 20, manteiga 1, chocolate 1, fermento 100 g
    Bolo de baunilha    5/dia  → farinha 2, açúcar 2, ovos 10, manteiga 1
    Brigadeiro (cento)  2/dia  → leite condensado 6 latas
    Torta de morango    4/dia  → morango 3 kg, creme de leite 4 caixas
    (a essência de baunilha não entra em nenhuma receita → consumo 0)

    Exemplo: farinha = 10 × 0,3 + 5 × 0,4 = 5 kg por dia.

Datas de lotes e pedidos são guardadas como "dias a partir de hoje" (e não como
datas fixas). Assim o cenário funciona em qualquer dia em que for povoado.

RESULTADOS_ESPERADOS é o gabarito: o que o agente DEVE responder para cada
ingrediente com os parâmetros padrão (folga 2 dias, cobertura 7, aviso 3).
O teste de integração (tests/test_cenarios.py) compara o agente com ele.
"""
from __future__ import annotations

# Colunas: id, nome, unidade, perecível, vida útil (dias), embalagem, prazo de entrega (dias)
INGREDIENTES = [
    (1,  "Farinha de trigo",     "kg",     False, None, 25,  3),   # saco de 25 kg
    (2,  "Manteiga",             "kg",     True,  10,   5,   2),   # perecível, dura 10 dias
    (3,  "Ovos",                 "un",     True,  20,   30,  1),   # bandeja de 30
    (4,  "Açúcar",               "kg",     False, None, 10,  2),
    (5,  "Chocolate em pó",      "kg",     False, None, 1,   5),   # entrega demorada: 5 dias
    (6,  "Leite condensado",     "lata",   False, None, 27,  3),   # caixa com 27 latas
    (7,  "Morango",              "kg",     True,  4,    2,   1),   # estraga em 4 dias
    (8,  "Creme de leite",       "caixa",  True,  90,   24,  2),
    (9,  "Fermento",             "g",      False, None, 500, 4),   # medido em gramas
    (10, "Essência de baunilha", "frasco", False, None, 1,   7),   # fora do cardápio
]

# Colunas: id, nome, vendas por dia, receita {id do ingrediente: quantidade por unidade}
PRODUTOS = [
    (1, "Bolo de chocolate", 10, {1: 0.3, 4: 0.2, 3: 2, 2: 0.1, 5: 0.1, 9: 10}),
    (2, "Bolo de baunilha",   5, {1: 0.4, 4: 0.4, 3: 2, 2: 0.2}),
    (3, "Brigadeiro (cento)", 2, {6: 3}),
    (4, "Torta de morango",   4, {7: 0.75, 8: 1}),
]

# Colunas: id do ingrediente, quantidade, dias até vencer (negativo = já venceu)
LOTES = [
    (1, 22,   120),   # farinha: 22 kg
    (2, 4,    2),     # manteiga: lote que vence em 2 dias → aviso R11
    (2, 2,    9),
    (3, 40,   15),    # ovos: só 40, abaixo da folga de 60
    (4, 30,   365),   # açúcar: estoque confortável
    # chocolate em pó (5): nenhum lote → estoque zero → EM FALTA
    (6, 10,   200),   # leite condensado: abaixo da folga → CRÍTICO
    (7, 7,    3),     # morango: vence em 3 dias → aviso R11
    (7, 2,    -1),    # morango: JÁ VENCIDO → não conta no estoque e gera aviso R12
    (8, 12,   40),
    (9, 500,  180),
    (10, 3,   300),
]

# Colunas: id do ingrediente, quantidade, há quantos dias foi feito, status
PEDIDOS = [
    (3, 300, 1, "pendente"),   # ovos a caminho: o agente NÃO deve mandar comprar de novo
    (8, 24,  1, "pendente"),   # creme de leite a caminho: por causa dele fica OK
    (1, 50,  10, "recebido"),  # pedido antigo já entregue: deve ser IGNORADO
]

# Quantos dias de vendas o povoar.py grava (e o repositório usa na média).
JANELA_DIAS = 28

# Gabarito. Para cada ingrediente:
# (situação, sugestão final de compra ou None, regras disparadas na ordem)
RESULTADOS_ESPERADOS = {
    "Farinha de trigo":     ("REPOR",    50,   ("R4", "R6", "R9", "R10")),
    "Manteiga":             ("REPOR",    20,   ("R4", "R6", "R8", "R10", "R11")),
    "Ovos":                 ("CRÍTICO",  None, ("R3", "R7")),
    "Açúcar":               ("OK",       None, ("R5",)),
    "Chocolate em pó":      ("EM FALTA", 14,   ("R2", "R6", "R9", "R10")),
    "Leite condensado":     ("CRÍTICO",  81,   ("R3", "R6", "R9", "R10")),
    "Morango":              ("REPOR",    12,   ("R4", "R6", "R8", "R10", "R11", "R12")),
    "Creme de leite":       ("OK",       None, ("R5",)),
    "Fermento":             ("REPOR",    1000, ("R4", "R6", "R9", "R10")),
    "Essência de baunilha": ("SEM USO",  None, ("R1",)),
}
"""Formatação das saídas do agente para o terminal (os ATUADORES).

Para que serve
--------------
O agente devolve objetos Recomendacao (definidos no contrato, em
agente/dominio/recomendacao.py). Este arquivo transforma esses objetos em
texto legível:

- formatar_numero(50.0)    → "50"      e  formatar_numero(0.75) → "0,75"
- tabela_recomendacoes()   → a tabela com situação, compra e regras + os avisos
- lista_de_compras()       → só o que precisa ser comprado
- tabela_regras()          → as 12 regras da base de conhecimento (para apresentar)

Como foi feito
--------------
Funções simples, sem classes, porque não há estado para guardar. Todas usam uma
função interna _tabela(), que alinha as colunas pela palavra mais larga.
Nada aqui decide coisa alguma: só formata o que o agente já decidiu.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from agente.conhecimento.regra import Regra          # só para o tipo de tabela_regras
from agente.dominio.recomendacao import Recomendacao

# Um "ícone" em texto para cada situação, para a tabela ser lida de relance.
ICONES = {"EM FALTA": "[!!]", "CRÍTICO": "[! ]", "REPOR": "[> ]", "OK": "[ok]", "SEM USO": "[--]"}


def formatar_numero(valor: float | None) -> str:
    """Número no jeito brasileiro e sem zeros inúteis: 50.0 → '50', 0.75 → '0,75'."""
    if valor is None:
        return "-"
    # :.3f garante no máximo 3 casas; rstrip tira os zeros e o ponto que sobrarem.
    texto = f"{valor:.3f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _tabela(cabecalho: Sequence[str], linhas: Sequence[Sequence[str]]) -> str:
    """Monta uma tabela de texto com as colunas alinhadas."""
    # zip(cabecalho, *linhas) agrupa os valores por COLUNA; a largura de cada
    # coluna é o tamanho do maior texto dela.
    larguras = [max(len(str(x)) for x in coluna) for coluna in zip(cabecalho, *linhas)]

    def linha(valores: Sequence[str]) -> str:
        # ljust completa cada valor com espaços até a largura da coluna.
        return "  ".join(str(v).ljust(w) for v, w in zip(valores, larguras)).rstrip()

    separador = "  ".join("-" * w for w in larguras)
    return "\n".join([linha(cabecalho), separador, *(linha(l) for l in linhas)])


def tabela_recomendacoes(recs: Iterable[Recomendacao]) -> str:
    """Tabela com todos os ingredientes e, embaixo, todos os avisos."""
    recs = list(recs)   # pode chegar um gerador; list() permite percorrer duas vezes
    linhas = []
    for r in recs:
        compra = f"{formatar_numero(r.sugestao_compra)} {r.unidade}" if r.precisa_comprar else "-"
        linhas.append([ICONES.get(str(r.situacao), ""), r.ingrediente, str(r.situacao), compra,
                       " ".join(r.regras_disparadas)])
    texto = _tabela(["", "Ingrediente", "Situação", "Comprar", "Regras"], linhas)
    avisos = [f"  - {r.ingrediente}: {a}" for r in recs for a in r.avisos]
    if avisos:
        texto += "\n\nAvisos:\n" + "\n".join(avisos)
    return texto


def lista_de_compras(recs: Iterable[Recomendacao]) -> str:
    """Só os ingredientes com sugestão de compra, prontos para virar um pedido."""
    itens = [r for r in recs if r.precisa_comprar]
    if not itens:
        return "Nada a comprar hoje."
    return "Lista de compras:\n" + "\n".join(
        f"  - {formatar_numero(r.sugestao_compra)} {r.unidade} de {r.ingrediente} ({r.situacao})"
        for r in itens
    )


def tabela_regras(regras: Iterable[Regra]) -> str:
    """As regras da base de conhecimento, com a forma matemática e em palavras."""
    return _tabela(["Regra", "Grupo", "Forma matemática", "Em palavras"],
                   [[r.id, str(r.grupo), r.formula, r.descricao] for r in regras])
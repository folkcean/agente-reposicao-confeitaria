"""Explicador: responde "por que o agente concluiu isso?".

Usa encadeamento para trás sobre o grafo de
dependências que ficou gravado na memória: parte do fato que se quer
explicar (o objetivo), descobre qual regra ou cálculo o produziu, e repete
para cada fato de que ele dependeu, até chegar aos sensores e aos parâmetros.

Exemplo de saída para a farinha:

    S2 (sugestão final) = 50   ← regra R10: S₁ existe → S₂ = ⌈S₁ ÷ B⌉ × B
    ├── S1 (sugestão ajustada) = 38   ← regra R9: ...
    │   ├── S0 (sugestão inicial) = 38   ← regra R6: ...
    ...
"""
from __future__ import annotations

from typing import Any

from agente.conhecimento.base import BaseDeConhecimento
from agente.conhecimento.fatos import MemoriaDeTrabalho

NOMES = {
    "c": "consumo por dia", "E": "estoque útil", "P": "a caminho", "L": "prazo de entrega",
    "C": "dias de cobertura", "F": "folga", "N": "nível mínimo", "Q": "quanto comprar",
    "V": "vida útil", "B": "embalagem", "A": "aviso de validade", "s": "situação",
    "S0": "sugestão inicial", "S1": "sugestão ajustada", "S2": "sugestão final",
    "D": "dias até a ruptura", "M": "margem para pedir",
    "perecivel": "perecível", "lotes": "lotes",
    "aviso_pedido_a_caminho": "aviso de pedido a caminho",
    "lotes_usar_primeiro": "lotes para usar primeiro", "lotes_vencidos": "lotes vencidos",
}

# Pedaços que desenham a árvore
RAMO_DO_MEIO = "├── "
RAMO_DO_FIM = "└── "
CONTINUA_A_LINHA = "│   "
ESPACO_VAZIO = "    "


def _e_tupla_de_lotes(valor: Any) -> bool:
    """Uma tupla não vazia cujos itens são lotes (têm dias_para_vencer)."""
    if not isinstance(valor, tuple):
        return False
    if len(valor) == 0:
        return False
    return hasattr(valor[0], "dias_para_vencer")


def formatar_valor(valor: Any) -> str:
    """Valor legível: 50.0 → '50', True → 'sim', lotes → 'id:qtd(dias d)'."""
    if isinstance(valor, bool):
        if valor:
            return "sim"
        return "não"

    if isinstance(valor, float):
        return f"{valor:g}"

    if _e_tupla_de_lotes(valor):
        descricoes_dos_lotes: list[str] = []
        for lote in valor:
            descricoes_dos_lotes.append(
                f"lote {lote.id}: {lote.quantidade:g} (vence em {lote.dias_para_vencer} d)"
            )
        return ", ".join(descricoes_dos_lotes)

    if isinstance(valor, tuple):
        itens_em_texto: list[str] = []
        for item in valor:
            itens_em_texto.append(str(item))
        texto = ", ".join(itens_em_texto)
        if texto == "":
            return "nenhum"
        return texto

    return str(valor)


class Explicador:
    """Monta a árvore de justificativa de um fato."""

    def __init__(self, base: BaseDeConhecimento) -> None:
        self.base = base

    def _origem_legivel(self, origem: str) -> str:
        """Para 'regra R4', devolve 'regra R4: <fórmula>'; outras origens ficam iguais."""
        if origem.startswith("regra "):
            regra_id = origem.removeprefix("regra ")
            regra = self.base.regra(regra_id)
            return f"regra {regra.id}: {regra.formula}"
        return origem

    def explicar(self, memoria: MemoriaDeTrabalho, objetivo: str) -> str:
        """Texto com a árvore de justificativa do fato `objetivo`."""
        if objetivo not in memoria:
            return f"O fato '{objetivo}' não foi concluído nesta avaliação."
        linhas: list[str] = []
        ja_explicados: set[str] = set()

        def visitar(nome: str, prefixo: str, conector: str) -> None:
            fato = memoria.fato(nome)
            nome_legivel = NOMES.get(nome, nome)
            rotulo = f"{nome} ({nome_legivel}) = {formatar_valor(fato.valor)}"

            # Um fato calculado que já apareceu não tem a subárvore repetida.
            tem_dependencias = len(fato.dependencias) > 0
            if nome in ja_explicados and tem_dependencias:
                linhas.append(f"{prefixo}{conector}{rotulo}   (já explicado acima)")
                return

            ja_explicados.add(nome)
            linhas.append(f"{prefixo}{conector}{rotulo}   ← {self._origem_legivel(fato.origem)}")

            filhos: list[str] = []
            for dependencia in fato.dependencias:
                if dependencia in memoria:
                    filhos.append(dependencia)

            # O prefixo dos filhos continua a linha vertical só se este fato não for o último.
            if conector == "":
                novo_prefixo = prefixo
            elif conector == RAMO_DO_MEIO:
                novo_prefixo = prefixo + CONTINUA_A_LINHA
            else:
                novo_prefixo = prefixo + ESPACO_VAZIO

            for posicao, filho in enumerate(filhos):
                e_o_ultimo = posicao == len(filhos) - 1
                if e_o_ultimo:
                    conector_do_filho = RAMO_DO_FIM
                else:
                    conector_do_filho = RAMO_DO_MEIO
                visitar(filho, novo_prefixo, conector_do_filho)

        visitar(objetivo, "", "")
        return "\n".join(linhas)

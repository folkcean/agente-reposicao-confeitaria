"""Modelos de dados de entrada do agente.

Contém apenas DADOS, sem nenhuma regra de negócio:

- Lote:        uma entrada de mercadoria com quantidade e validade.
- Ingrediente: tudo o que o agente percebe sobre um ingrediente, já lido do
               banco (consumo médio, prazo de entrega, embalagem, lotes...).
- Parametros:  valores que o usuário pode ajustar (dias de folga etc.).

Quem preenche Ingrediente é o repositório (pasta dados/). Quem usa é o
estado interno (agente/estado/). As classes são imutáveis (frozen) para
garantir que o agente nunca altere uma percepção por engano.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Lote:
    """Uma entrada de mercadoria no estoque.

    Atributos:
        id: identificador do lote no banco.
        quantidade: quanto resta deste lote, na unidade do ingrediente.
        validade: data de validade do lote.
    """

    id: int
    quantidade: float
    validade: date

    def __post_init__(self) -> None:
        if self.quantidade < 0:
            raise ValueError(f"Lote {self.id}: quantidade não pode ser negativa")

    def dias_para_vencer(self, hoje: date) -> int:
        """Dias até vencer. Zero ou negativo significa que já venceu."""
        return (self.validade - hoje).days


@dataclass(frozen=True)
class Ingrediente:
    """
    Atributos (entre parênteses, o símbolo usado nas regras):
        id, nome, unidade: identificação.
        consumo_diario (c): média de consumo por dia na janela de vendas.
        prazo_entrega_dias (L): dias que o fornecedor leva para entregar.
        embalagem (B): tamanho da embalagem de compra.
        perecivel: se o ingrediente estraga rápido.
        vida_util_dias (V): dias que o produto dura; None se não perecível.
        a_caminho (P): quantidade pedida e ainda não entregue.
        lotes: lotes em estoque.
    """

    id: int
    nome: str
    unidade: str
    consumo_diario: float
    prazo_entrega_dias: int
    embalagem: float
    perecivel: bool
    vida_util_dias: int | None
    a_caminho: float = 0.0
    lotes: tuple[Lote, ...] = ()

    def __post_init__(self) -> None:
        if self.consumo_diario < 0:
            raise ValueError(f"{self.nome}: consumo diário não pode ser negativo")
        if self.prazo_entrega_dias < 0:
            raise ValueError(f"{self.nome}: prazo de entrega não pode ser negativo")
        if self.embalagem <= 0:
            raise ValueError(f"{self.nome}: embalagem deve ser maior que zero")
        if self.a_caminho < 0:
            raise ValueError(f"{self.nome}: quantidade a caminho não pode ser negativa")
        if self.perecivel and (self.vida_util_dias is None or self.vida_util_dias <= 0):
            raise ValueError(f"{self.nome}: perecível precisa de vida útil > 0")


@dataclass(frozen=True)
class Parametros:
    """Parâmetros ajustáveis pelo usuário """
    dias_folga: int = 2
    dias_cobertura: int = 7
    aviso_validade_dias: int = 3
    janela_consumo_dias: int = 28

    def __post_init__(self) -> None:
        # Folga >= 1 garante F > 0 sempre que c > 0. Com folga 0, um ingrediente
        # com estoque zero satisfaria R2 (EM FALTA) e R4 (REPOR) ao mesmo tempo.
        if self.dias_folga < 1:
            raise ValueError("dias_folga deve ser pelo menos 1")
        for nome in ("dias_cobertura", "aviso_validade_dias"):
            if getattr(self, nome) < 0:
                raise ValueError(f"{nome} não pode ser negativo")
        if self.janela_consumo_dias <= 0:
            raise ValueError("janela_consumo_dias deve ser maior que zero")

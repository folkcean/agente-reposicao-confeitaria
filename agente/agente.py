"""O agente completo: AgenteReposicao.

Liga todas as partes, seguindo o ciclo de um agente reativo baseado em
modelo:

    percepção (repositório) → estado interno → regras (motor) → ação (recomendação)

Uso típico:
    agente = AgenteReposicao(repositorio)
    for rec in agente.avaliar_todos(date.today()):
        print(rec.ingrediente, rec.situacao, rec.sugestao_compra)

O agente é reativo aos sensores: quando o sistema registra uma venda,
entrada ou pedido, chama-se reagir([ids afetados], hoje) e só esses
ingredientes são reavaliados.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from agente.conhecimento.base import BaseDeConhecimento
from agente.conhecimento.fatos import MemoriaDeTrabalho
from agente.dominio.modelos import Ingrediente, Parametros
from agente.dominio.recomendacao import Recomendacao, Situacao
from agente.dominio.repositorio import RepositorioEstoque
from agente.estado.estado_interno import EstadoInterno
from agente.inferencia.explicador import Explicador
from agente.inferencia.motor import Disparo, MotorDeInferencia

# Ordem de preferência do que explicar quando ninguém diz qual fato:
# a compra final, senão o aviso de pedido a caminho, senão a situação.
OBJETIVOS_PARA_EXPLICAR = ("S2", "aviso_pedido_a_caminho", "s")


@dataclass(frozen=True)
class Avaliacao:
    """Tudo o que aconteceu na avaliação de um ingrediente (para depuração)."""

    ingrediente: Ingrediente
    memoria: MemoriaDeTrabalho
    rastro: tuple[Disparo, ...]
    recomendacao: Recomendacao


def _ordem_de_urgencia(recomendacao: Recomendacao) -> tuple:
    """Chave de ordenação: primeiro a prioridade da situação, depois o nome."""
    return (recomendacao.situacao.prioridade, recomendacao.ingrediente)

def _dias_legivel(dias: float) -> str:
    """2.333 → '2,3'; 4.0 → '4' (uma casa, vírgula, sem ',0' no fim)."""
    texto = f"{dias:.1f}".replace(".", ",")
    if texto.endswith(",0"):
        texto = texto[:-2]
    return texto


def _aviso_de_prazo(memoria: MemoriaDeTrabalho, hoje: date) -> str:
    """Quando o estoque acaba e até quando dá para pedir sem faltar."""
    dias_ate_a_ruptura = memoria["D"]
    margem_para_pedir = memoria["M"]
    prazo_de_entrega = memoria["L"]

    if margem_para_pedir < 0:
        dias_em_falta = -margem_para_pedir
        if dias_ate_a_ruptura == 0:
            inicio = "Já acabou"
        else:
            inicio = f"Acaba em {_dias_legivel(dias_ate_a_ruptura)} dia(s)"
        return (
            f"{inicio} e a entrega leva {prazo_de_entrega} dia(s): "
            f"deve faltar por cerca de {_dias_legivel(dias_em_falta)} dia(s), mesmo pedindo hoje."
        )

    dias_ate_o_prazo = math.floor(margem_para_pedir)
    prazo = hoje + timedelta(days=dias_ate_o_prazo)
    if dias_ate_o_prazo == 0:
        quando_pedir = f"peça hoje ({prazo:%d/%m})"
    else:
        quando_pedir = f"peça até {prazo:%d/%m}"
    return (
        f"Acaba em {_dias_legivel(dias_ate_a_ruptura)} dia(s) no ritmo atual: "
        f"{quando_pedir} para a entrega chegar antes."
    )

def _ids_das_regras(rastro: Iterable[Disparo]) -> list[str]:
    """Ids das regras do rastro, na ordem em que dispararam."""
    ids: list[str] = []
    for disparo in rastro:
        ids.append(disparo.regra_id)
    return ids


class AgenteReposicao:
    """Agente reativo baseado em modelo, implementado como sistema especialista."""

    def __init__(
        self,
        repositorio: RepositorioEstoque,
        base: BaseDeConhecimento | None = None,
        parametros: Parametros | None = None,
    ) -> None:
        self.repositorio = repositorio

        # Sem base (ou com uma base vazia), usa as 12 regras do projeto.
        if base is None or len(base) == 0:
            self.base = BaseDeConhecimento.padrao()
        else:
            self.base = base

        if parametros is None:
            self.parametros = Parametros()
        else:
            self.parametros = parametros

        self.motor = MotorDeInferencia(self.base)
        self.explicador = Explicador(self.base)

    #avaliação
    def avaliar(self, ingrediente: Ingrediente, hoje: date) -> Avaliacao:
        """Avalia um ingrediente já carregado: estado interno → motor → recomendação."""
        memoria = EstadoInterno(ingrediente, self.parametros, hoje).para_memoria()
        rastro = tuple(self.motor.executar(memoria))
        recomendacao = self._recomendacao(ingrediente, memoria, rastro, hoje)
        return Avaliacao(ingrediente, memoria, rastro, recomendacao)

    def avaliar_todos(self, hoje: date) -> list[Recomendacao]:
        """Avalia todos os ingredientes, do mais urgente para o menos urgente."""
        recomendacoes: list[Recomendacao] = []
        for ingrediente in self.repositorio.listar_ingredientes(hoje):
            avaliacao = self.avaliar(ingrediente, hoje)
            recomendacoes.append(avaliacao.recomendacao)
        return sorted(recomendacoes, key=_ordem_de_urgencia)

    def avaliar_ingrediente(self, ingrediente_id: int, hoje: date) -> Recomendacao:
        ingrediente = self._buscar(ingrediente_id, hoje)
        avaliacao = self.avaliar(ingrediente, hoje)
        return avaliacao.recomendacao

    def reagir(self, ingredientes_afetados: Iterable[int], hoje: date) -> list[Recomendacao]:
        """Reavalia só os ingredientes afetados por um evento (venda, entrada, pedido).

        Um id repetido é avaliado uma vez só, na posição em que apareceu primeiro.
        """
        ids_sem_repeticao: list[int] = []
        for ingrediente_id in ingredientes_afetados:
            if ingrediente_id not in ids_sem_repeticao:
                ids_sem_repeticao.append(ingrediente_id)

        recomendacoes: list[Recomendacao] = []
        for ingrediente_id in ids_sem_repeticao:
            recomendacoes.append(self.avaliar_ingrediente(ingrediente_id, hoje))
        return recomendacoes

    #explicação
    def explicar(self, ingrediente_id: int, hoje: date, objetivo: str | None = None) -> str:
        """Explica a conclusão principal: S2 se houver compra, o aviso de pedido
        a caminho se houver, senão a situação s."""
        avaliacao = self.avaliar(self._buscar(ingrediente_id, hoje), hoje)

        if objetivo is None:
            for candidato in OBJETIVOS_PARA_EXPLICAR:
                if candidato in avaliacao.memoria:
                    objetivo = candidato
                    break

        regras_disparadas = ", ".join(_ids_das_regras(avaliacao.rastro))
        cabecalho = f"Por que {avaliacao.ingrediente.nome}? (regras disparadas: {regras_disparadas})"
        arvore = self.explicador.explicar(avaliacao.memoria, objetivo)
        return cabecalho + "\n" + arvore

    #auxiliares
    def _buscar(self, ingrediente_id: int, hoje: date) -> Ingrediente:
        ingrediente = self.repositorio.buscar_ingrediente(ingrediente_id, hoje)
        if ingrediente is None:
            raise KeyError(f"Ingrediente {ingrediente_id} não encontrado")
        return ingrediente

    @staticmethod
    def _recomendacao(
        ingrediente: Ingrediente, memoria: MemoriaDeTrabalho, rastro: tuple[Disparo, ...], hoje: date
    ) -> Recomendacao:
        unidade = ingrediente.unidade
        avisos: list[str] = []
        # Prazo-limite: só para o que entrou na lista de compras
        sugestao_final = memoria.get("S2")
        vai_comprar = sugestao_final is not None and sugestao_final > 0
        if vai_comprar and "M" in memoria:
            avisos.append(_aviso_de_prazo(memoria, hoje))


        # R7: o pedido a caminho já cobre a necessidade
        if memoria.get("aviso_pedido_a_caminho"):
            a_caminho = memoria["P"]
            avisos.append(f"Já há {a_caminho:g} {unidade} a caminho, que cobrem a necessidade: acompanhe a entrega.")

        lotes_por_id = {}
        for lote in memoria["lotes"]:
            lotes_por_id[lote.id] = lote

        # R11: lotes que vencem logo
        for lote_id in memoria.get("lotes_usar_primeiro", ()):
            lote = lotes_por_id[lote_id]
            avisos.append(
                f"Lote {lote.id} ({lote.quantidade:g} {unidade}) vence em {lote.dias_para_vencer} dia(s): use primeiro."
            )

        # R12: lotes vencidos
        for lote_id in memoria.get("lotes_vencidos", ()):
            lote = lotes_por_id[lote_id]
            avisos.append(f"Lote {lote.id} ({lote.quantidade:g} {unidade}) está vencido: descarte.")

        situacao = memoria.get("s", Situacao.SEM_USO)
        return Recomendacao(
            ingrediente_id=ingrediente.id,
            ingrediente=ingrediente.nome,
            unidade=unidade,
            situacao=situacao,
            sugestao_compra=memoria.get("S2"),
            avisos=tuple(avisos),
            regras_disparadas=tuple(_ids_das_regras(rastro)),
        )

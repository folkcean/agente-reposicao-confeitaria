"""Simulação para medir o desempenho do agente (medida P da matriz PEAS).

O que faz
---------
Simula 90 dias de operação da confeitaria de exemplo (dados/cenarios.py) e
compara três políticas de reposição, todas vendo o MESMO mundo (mesma demanda
e mesmos atrasos, graças à semente aleatória):

    agente    → o AgenteReposicao (estado interno + 12 regras + motor).
    if/else   → regra fixa no código: "se estoque < mínimo fixo, compre Q fixo".
                O mínimo é calculado uma vez com o consumo nominal e nunca muda;
                não considera pedidos a caminho nem validade.
    operador  → compra só quando o estoque está para acabar (menos de 1 dia),
                sem olhar validade; lembra que já pediu (não pede de novo).

Ciclo de cada dia (para cada ingrediente):
    1. chegam os pedidos cujo prazo venceu  → viram lotes novos;
    2. lotes vencidos são descartados       → contam como desperdício;
    3. a política decide se compra          → pedido com prazo real de entrega;
    4. a demanda do dia é consumida (lote que vence primeiro sai primeiro);
       o que não pôde ser atendido conta como ruptura.

Medidas (ligadas à medida de desempenho P da Fase 1):
    nível de serviço, dias em ruptura, compras emergenciais (feitas com o
    estoque já zerado), desperdício de perecíveis, folga do pedido
    (E/c − L no dia do pedido: >= 0 significa que o pedido chega antes de acabar)
    e estoque médio em dias de cobertura.

Só usa a biblioteca padrão (random, math, statistics, time).

Como rodar:
    python -m experimentos.simulacao            # 30 repetições, imprime as tabelas
    python -m experimentos.simulacao --rep 5    # mais rápido
    python -m experimentos.simulacao --sensibilidade   # varia os dias de folga do agente
"""
from __future__ import annotations

import argparse
import math
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import date, timedelta

from agente.agente import AgenteReposicao
from agente.dominio.modelos import Ingrediente, Lote, Parametros
from agente.dominio.repositorio import RepositorioMemoria
from dados.cenarios import INGREDIENTES, PRODUTOS

INICIO = date(2026, 9, 1)
DIAS = 90
JANELA = 28
VALIDADE_NAO_PERECIVEL = 365


# ---------------------------------------------------------------- mundo
@dataclass(frozen=True)
class Cenario:
    """Como o mundo se comporta: ruído da demanda, pico e atrasos de entrega."""

    nome: str
    ruido: float = 0.2                    # desvio relativo das vendas diárias
    pico: tuple[int, int, float] | None = None   # (dia inicial, dia final, fator)
    atrasos: tuple[int, ...] = (0,)       # dias extras sorteados em cada entrega


CENARIOS = [
    Cenario("Normal"),
    Cenario("Pico de demanda", pico=(45, 60, 1.6)),
    Cenario("Fornecedor instável", atrasos=(0, 0, 1, 2, 3)),
]


def _receitas() -> dict[int, float]:
    """Consumo nominal por dia de cada ingrediente (vendas médias × receita)."""
    nominal: dict[int, float] = {i[0]: 0.0 for i in INGREDIENTES}
    for _pid, _nome, vendas, receita in PRODUTOS:
        for ing_id, qtd in receita.items():
            nominal[ing_id] += vendas * qtd
    return nominal


def gerar_demanda(cenario: Cenario, semente: int) -> dict[int, list[float]]:
    """Demanda diária de cada ingrediente: JANELA dias de histórico + DIAS simulados."""
    rnd = random.Random(semente)
    total = JANELA + DIAS
    demanda = {i[0]: [0.0] * total for i in INGREDIENTES}
    for dia in range(total):
        fator = 1.0
        if cenario.pico and cenario.pico[0] <= dia - JANELA <= cenario.pico[1]:
            fator = cenario.pico[2]
        for _pid, _nome, vendas, receita in PRODUTOS:
            vendidos = max(0, round(rnd.gauss(vendas * fator, vendas * cenario.ruido)))
            for ing_id, qtd in receita.items():
                demanda[ing_id][dia] += vendidos * qtd
    return demanda


# ---------------------------------------------------------------- políticas
class Politica:
    nome = ""

    def decidir(self, ing: Ingrediente, hoje: date) -> float:
        """Quantidade a comprar hoje (0 = não compra)."""
        raise NotImplementedError


class PoliticaAgente(Politica):
    nome = "Agente (sistema especialista)"

    def __init__(self, parametros: Parametros | None = None) -> None:
        self.agente = AgenteReposicao(RepositorioMemoria(), parametros=parametros)

    def decidir(self, ing: Ingrediente, hoje: date) -> float:
        rec = self.agente.avaliar(ing, hoje).recomendacao
        return rec.sugestao_compra if rec.precisa_comprar else 0.0


class PoliticaIfElse(Politica):
    nome = "if/else com mínimo fixo"

    def __init__(self, nominal: dict[int, float]) -> None:
        self.nominal = nominal

    def decidir(self, ing: Ingrediente, hoje: date) -> float:
        c0 = self.nominal[ing.id]
        estoque = sum(l.quantidade for l in ing.lotes if l.validade > hoje)
        if c0 > 0 and estoque < c0 * (ing.prazo_entrega_dias + 2):
            return math.ceil(c0 * (ing.prazo_entrega_dias + 7) / ing.embalagem) * ing.embalagem
        return 0.0


class PoliticaOperador(Politica):
    nome = "Operador (compra quando acaba)"

    def __init__(self, nominal: dict[int, float]) -> None:
        self.nominal = nominal

    def decidir(self, ing: Ingrediente, hoje: date) -> float:
        c0 = self.nominal[ing.id]
        estoque = sum(l.quantidade for l in ing.lotes if l.validade > hoje)
        if c0 > 0 and ing.a_caminho == 0 and estoque < c0:
            return math.ceil(c0 * (ing.prazo_entrega_dias + 7) / ing.embalagem) * ing.embalagem
        return 0.0


# ---------------------------------------------------------------- medição
@dataclass
class Medidas:
    demanda: float = 0.0
    atendida: float = 0.0
    dias_ruptura: int = 0
    compras: int = 0
    emergenciais: int = 0
    comprado_perecivel: float = 0.0
    vencido_perecivel: float = 0.0
    folgas_pedido: list[float] = field(default_factory=list)
    cobertura: list[float] = field(default_factory=list)


@dataclass
class _Pedido:
    quantidade: float
    chegada: int


def simular(politica: Politica, cenario: Cenario, semente: int) -> dict[int, Medidas]:
    """Roda DIAS dias e devolve as medidas de cada ingrediente consumido."""
    demanda = gerar_demanda(cenario, semente)
    nominal = _receitas()
    rnd_atraso = random.Random(semente * 7919 + 1)
    medidas: dict[int, Medidas] = {}

    for (ing_id, nome, unidade, perecivel, vida, emb, prazo) in INGREDIENTES:
        if nominal[ing_id] == 0:
            continue
        m = medidas[ing_id] = Medidas()
        validade = vida if perecivel else VALIDADE_NAO_PERECIVEL
        # estoque inicial igual para todas as políticas: 5 dias de consumo, fresco
        lotes: list[list] = [[nominal[ing_id] * 5, 0 + min(validade, 30)]]   # [qtd, dia em que vence]
        pedidos: list[_Pedido] = []
        proximo_lote = 1

        for d in range(DIAS):
            hoje = INICIO + timedelta(days=d)
            # 1. chegam pedidos
            for p in [p for p in pedidos if p.chegada == d]:
                lotes.append([p.quantidade, d + validade])
                pedidos.remove(p)
            # 2. descarta vencidos
            for lote in [l for l in lotes if l[1] <= d]:
                if perecivel:
                    m.vencido_perecivel += lote[0]
                lotes.remove(lote)
            # 3. percepção + decisão
            historico = demanda[ing_id][d : d + JANELA]       # últimos 28 dias
            consumo = sum(historico) / JANELA
            estoque = sum(l[0] for l in lotes)
            percepcao = Ingrediente(
                id=ing_id, nome=nome, unidade=unidade, consumo_diario=round(consumo, 3),
                prazo_entrega_dias=prazo, embalagem=emb, perecivel=perecivel,
                vida_util_dias=vida, a_caminho=sum(p.quantidade for p in pedidos),
                lotes=tuple(Lote(proximo_lote + k, max(0.0, l[0]), INICIO + timedelta(days=l[1]))
                            for k, l in enumerate(lotes)),
            )
            proximo_lote += len(lotes)
            qtd = politica.decidir(percepcao, hoje)
            if qtd > 0:
                m.compras += 1
                if estoque <= 1e-9:
                    m.emergenciais += 1
                m.folgas_pedido.append(estoque / nominal[ing_id] - prazo)
                atraso = rnd_atraso.choice(cenario.atrasos)
                pedidos.append(_Pedido(qtd, d + prazo + atraso))
                if perecivel:
                    m.comprado_perecivel += qtd
            # 4. demanda do dia (lote que vence primeiro sai primeiro)
            pedido_dia = demanda[ing_id][d + JANELA]
            m.demanda += pedido_dia
            falta = pedido_dia
            for lote in sorted(lotes, key=lambda l: l[1]):
                usa = min(lote[0], falta)
                lote[0] -= usa
                falta -= usa
            lotes = [l for l in lotes if l[0] > 1e-9]
            m.atendida += pedido_dia - falta
            if falta > 1e-9:
                m.dias_ruptura += 1
            m.cobertura.append(sum(l[0] for l in lotes) / nominal[ing_id])
    return medidas


def resumir(resultados: list[dict[int, Medidas]]) -> dict[str, float]:
    """Média das repetições, somando os 9 ingredientes consumidos."""
    linhas = []
    for med in resultados:
        todos = list(med.values())
        pereciveis = [m for m in todos if m.comprado_perecivel > 0]
        folgas = [f for m in todos for f in m.folgas_pedido]
        linhas.append({
            "servico": 100 * sum(m.atendida for m in todos) / sum(m.demanda for m in todos),
            "dias_ruptura": sum(m.dias_ruptura for m in todos),
            "compras": sum(m.compras for m in todos),
            "emergenciais": sum(m.emergenciais for m in todos),
            "desperdicio": 100 * statistics.mean(m.vencido_perecivel / m.comprado_perecivel for m in pereciveis)
                           if pereciveis else 0.0,
            "pedidos_a_tempo": 100 * sum(f >= 0 for f in folgas) / len(folgas) if folgas else 0.0,
            "cobertura": statistics.mean(c for m in todos for c in m.cobertura),
        })
    return {k: statistics.mean(l[k] for l in linhas) for k in linhas[0]}


def medir_tempo() -> list[tuple[int, float, float]]:
    """Tempo de avaliar_todos para 10, 100, 1.000 e 10.000 ingredientes."""
    from dados.cenarios import INGREDIENTES as BASE
    nominal = _receitas()
    hoje = INICIO
    saida = []
    for n in (10, 100, 1000, 10000):
        ings = []
        for k in range(n):
            ing_id, nome, unidade, perecivel, vida, emb, prazo = BASE[k % len(BASE)]
            ings.append(Ingrediente(
                id=k + 1, nome=f"{nome} {k}", unidade=unidade, consumo_diario=nominal[ing_id],
                prazo_entrega_dias=prazo, embalagem=emb, perecivel=perecivel, vida_util_dias=vida,
                lotes=(Lote(k + 1, nominal[ing_id] * 3, hoje + timedelta(days=vida or 100)),)))
        agente = AgenteReposicao(RepositorioMemoria(ings))
        inicio = time.perf_counter()
        agente.avaliar_todos(hoje)
        total = time.perf_counter() - inicio
        saida.append((n, total * 1000, total * 1000 / n))
    return saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Experimentos de desempenho do agente")
    parser.add_argument("--rep", type=int, default=30, help="repetições por cenário (sementes)")
    parser.add_argument("--sensibilidade", action="store_true",
                        help="também varia os dias de folga do agente (1 a 5)")
    args = parser.parse_args(argv)
    nominal = _receitas()
    politicas = [PoliticaAgente, lambda: PoliticaIfElse(nominal), lambda: PoliticaOperador(nominal)]

    cab = f"{'Cenário':<20} {'Política':<32} {'Serviço%':>8} {'DiasRupt':>8} {'Compras':>7} {'Emerg.':>6} {'Desp.%':>6} {'ATempo%':>7} {'Cob.(d)':>7}"
    print(f"{DIAS} dias, {args.rep} repetições por cenário, 9 ingredientes consumidos\n")
    print(cab)
    print("-" * len(cab))
    for cenario in CENARIOS:
        for fabrica in politicas:
            pol = fabrica()
            r = resumir([simular(pol, cenario, s) for s in range(args.rep)])
            print(f"{cenario.nome:<20} {pol.nome:<32} {r['servico']:>8.1f} {r['dias_ruptura']:>8.1f} "
                  f"{r['compras']:>7.1f} {r['emergenciais']:>6.1f} {r['desperdicio']:>6.1f} "
                  f"{r['pedidos_a_tempo']:>7.1f} {r['cobertura']:>7.1f}")
        print()
    if args.sensibilidade:
        print("Sensibilidade: dias de folga do agente (dias em ruptura / desperdício %)")
        for cenario in CENARIOS:
            partes = []
            for folga in (1, 2, 3, 4, 5):
                pol = PoliticaAgente(Parametros(dias_folga=folga))
                r = resumir([simular(pol, cenario, s) for s in range(args.rep)])
                partes.append(f"folga {folga}: {r['dias_ruptura']:.1f} / {r['desperdicio']:.1f}")
            print(f"  {cenario.nome:<20} " + " | ".join(partes))
        print()
    print("Tempo de execução do agente (avaliar_todos):")
    for n, total, por in medir_tempo():
        print(f"  {n:>6} ingredientes: {total:8.1f} ms no total, {por:.3f} ms por ingrediente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
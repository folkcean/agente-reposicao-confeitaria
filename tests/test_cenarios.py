"""Teste de integração: banco + sensores + agente + interface juntos (tarefa D1).

Para que serve
--------------
É o teste que prova que as partes funcionam JUNTAS.
Ele povoa o banco com os 10 cenários, roda o agente de verdade e compara o
resultado de cada ingrediente com o gabarito em dados/cenarios.py
(RESULTADOS_ESPERADOS). Se ele passa, o projeto funciona de ponta a ponta.

Como foi feito
--------------
A fixture `recomendacoes` faz o caminho completo uma vez e devolve um
dicionário {nome do ingrediente: Recomendacao}. O parametrize gera um teste
separado por ingrediente, então se um falhar o pytest diz exatamente qual.
"""
import pytest

from agente.agente import AgenteReposicao
from dados.cenarios import RESULTADOS_ESPERADOS
from dados.conexao import abrir_conexao
from dados.povoar import povoar
from dados.repositorio_sqlite import RepositorioSQLite
from interface.console import lista_de_compras, tabela_recomendacoes


@pytest.fixture
def recomendacoes(hoje):
    conn = abrir_conexao(":memory:")
    povoar(conn, hoje)                                                  # dados 
    recs = AgenteReposicao(RepositorioSQLite(conn)).avaliar_todos(hoje)  # agente 
    conn.close()
    return {r.ingrediente: r for r in recs}


@pytest.mark.parametrize("nome", list(RESULTADOS_ESPERADOS))
def test_cenario(recomendacoes, nome):
    situacao, compra, regras = RESULTADOS_ESPERADOS[nome]
    r = recomendacoes[nome]
    assert str(r.situacao) == situacao
    assert r.sugestao_compra == compra
    assert r.regras_disparadas == regras


def test_todas_as_regras_sao_usadas_em_algum_cenario(recomendacoes):
    # Garante que os cenários exercitam a base de conhecimento inteira (R1 a R12).
    usadas = {regra for r in recomendacoes.values() for regra in r.regras_disparadas}
    assert usadas == {f"R{i}" for i in range(1, 13)}


def test_saida_no_terminal(recomendacoes):
    # Interface formatando o que o agente decidiu.
    texto = tabela_recomendacoes(recomendacoes.values())
    assert "Morango" in texto and "descarte" in texto
    assert "81 lata" in lista_de_compras(recomendacoes.values())
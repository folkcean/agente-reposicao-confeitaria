"""Testes da formatação no terminal e da linha de comando (tarefa B6).

Para que serve
--------------
Os três primeiros testes conferem as funções de interface/console.py com
recomendações montadas à mão (não precisam do agente nem do banco).
O último roda o programa inteiro de ponta a ponta, como se fosse no terminal.

Como foi feito
--------------
- tmp_path (fixture do pytest) é uma pasta temporária: o banco do teste é
  criado lá e apagado depois, sem sujar o projeto.
- capsys (fixture do pytest) captura o que o programa imprimiu com print(),
  para o teste poder conferir o texto.
"""
from agente.dominio.recomendacao import Recomendacao, Situacao
from interface.console import formatar_numero, lista_de_compras, tabela_recomendacoes
import main


def rec(nome, situacao, compra):
    """Recomendação de mentira, só para testar a formatação."""
    return Recomendacao(1, nome, "kg", situacao, compra, (), ("R4",))


def test_formatar_numero():
    assert [formatar_numero(x) for x in (50.0, 0.75, 1000, None)] == ["50", "0,75", "1000", "-"]


def test_lista_de_compras():
    assert lista_de_compras([rec("Açúcar", Situacao.OK, None)]) == "Nada a comprar hoje."
    assert "50 kg de Farinha" in lista_de_compras([rec("Farinha", Situacao.REPOR, 50)])


def test_tabela():
    assert "Farinha" in tabela_recomendacoes([rec("Farinha", Situacao.REPOR, 50)])


def test_cli_ponta_a_ponta(tmp_path, capsys):
    banco = str(tmp_path / "teste.db")
    assert main.main(["povoar", "--banco", banco, "--hoje", "2026-11-20"]) == 0
    assert main.main(["avaliar", "--banco", banco, "--hoje", "2026-11-20"]) == 0
    assert "Leite condensado" in capsys.readouterr().out
    assert main.main(["explicar", "morango", "--banco", banco, "--hoje", "2026-11-20"]) == 0
    assert "R8" in capsys.readouterr().out
    # Ingrediente que não existe: o programa avisa e devolve 1 (erro).
    assert main.main(["explicar", "pistache", "--banco", banco, "--hoje", "2026-11-20"]) == 1
    assert main.main(["regras"]) == 0
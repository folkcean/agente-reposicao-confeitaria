"""Ponto de entrada do projeto: a linha de comando.

Para que serve
--------------
É o arquivo que você roda no terminal. Ele liga as três partes do projeto:
os dados (banco e sensores), o agente do Iarlo e a interface (atuadores).

Comandos
--------
    python main.py povoar   [--banco ARQ] [--hoje AAAA-MM-DD]   cria o banco de exemplo
    python main.py avaliar  [--banco ARQ] [--hoje AAAA-MM-DD]   roda o agente em todos os ingredientes
    python main.py explicar NOME [--banco ARQ] [--hoje ...]     mostra por que o agente decidiu
    python main.py regras                                       lista a base de conhecimento

Demonstração completa:
    python main.py povoar --hoje 2026-11-20
    python main.py avaliar --hoje 2026-11-20
    python main.py explicar morango --hoje 2026-11-20

Como foi feito
--------------
Usa o módulo argparse (já vem com o Python), que lê o que foi digitado depois
de `python main.py` e gera a ajuda sozinho (`python main.py --help`).
A função main(argv) devolve 0 (deu certo) ou 1 (erro). Receber argv como
parâmetro permite que os testes chamem main(["avaliar", ...]) direto, sem
abrir um terminal.

Do agente, este arquivo usa só o que foi combinado no contrato (seção 6 do guia):
AgenteReposicao(repositorio), avaliar_todos, explicar e BaseDeConhecimento.padrao().
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from agente.agente import AgenteReposicao                    
from agente.conhecimento.base import BaseDeConhecimento       
from agente.dominio.modelos import Parametros               
from dados.conexao import BANCO_PADRAO, abrir_conexao        
from dados.povoar import povoar
from dados.repositorio_sqlite import RepositorioSQLite
from interface.console import lista_de_compras, tabela_recomendacoes, tabela_regras


def _data(texto: str) -> date:
    """Converte '2026-11-20' em data; mensagem amigável se o formato estiver errado."""
    try:
        return date.fromisoformat(texto)
    except ValueError as erro:
        raise argparse.ArgumentTypeError("use o formato AAAA-MM-DD") from erro


def criar_parser() -> argparse.ArgumentParser:
    """Define os comandos e opções que o programa aceita."""
    parser = argparse.ArgumentParser(description="Agente de reposição de estoque da confeitaria")
    sub = parser.add_subparsers(dest="comando", required=True)

    # povoar, avaliar e explicar aceitam as mesmas duas opções: --banco e --hoje.
    for nome, ajuda in [("povoar", "cria o banco com os 10 cenários"),
                        ("avaliar", "avalia todos os ingredientes"),
                        ("explicar", "explica a decisão para um ingrediente")]:
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("--banco", default=BANCO_PADRAO, help=f"arquivo do banco (padrão: {BANCO_PADRAO})")
        p.add_argument("--hoje", type=_data, default=date.today(), help="data de referência AAAA-MM-DD")
        if nome == "explicar":
            p.add_argument("ingrediente", help="nome ou parte do nome, ex.: farinha")

    # regras não precisa de banco.
    sub.add_parser("regras", help="lista as regras da base de conhecimento")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa o comando pedido. argv=None significa 'ler do terminal'."""
    args = criar_parser().parse_args(argv)

    if args.comando == "regras":
        print(tabela_regras(BaseDeConhecimento.padrao()))
        return 0

    conn = abrir_conexao(args.banco)
    try:   # try/finally garante que a conexão é fechada mesmo se der erro no meio
        if args.comando == "povoar":
            povoar(conn, args.hoje)
            print(f"Banco '{args.banco}' povoado com os cenários de exemplo (hoje = {args.hoje}).")
            return 0

        # Daqui para baixo precisamos do agente: sensores → agente.
        repositorio = RepositorioSQLite(conn, janela_dias=Parametros().janela_consumo_dias)
        agente = AgenteReposicao(repositorio)

        if args.comando == "avaliar":
            recs = agente.avaliar_todos(args.hoje)     # o agente decide
            print(f"Avaliação de {args.hoje}\n")
            print(tabela_recomendacoes(recs))          # os atuadores mostram
            print()
            print(lista_de_compras(recs))
            return 0

        if args.comando == "explicar":
            ingrediente = repositorio.buscar_por_nome(args.ingrediente, args.hoje)
            if ingrediente is None:
                print(f"Ingrediente '{args.ingrediente}' não encontrado.", file=sys.stderr)
                return 1
            print(agente.explicar(ingrediente.id, args.hoje))
            return 0
    finally:
        conn.close()
    return 1


# Só roda main() quando o arquivo é executado direto (python main.py ...),
# e não quando é importado pelos testes.
if __name__ == "__main__":
    sys.exit(main())
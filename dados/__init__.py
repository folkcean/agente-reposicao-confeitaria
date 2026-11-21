"""Pacote `dados`: a camada de DADOS do agente.

Para que serve
--------------
O agente não sabe de onde vêm os números que ele usa. Ele só pede
"me dê os ingredientes" a um objeto que siga a interface RepositorioEstoque
(definida em agente/dominio/repositorio.py, o contrato). Este pacote fornece
esse objeto, lendo um banco SQLite de demonstração.

Na matriz PEAS, esta pasta é o conjunto de SENSORES do agente.

Arquivos
--------
- schema.sql            "planta" do banco: as seis tabelas e suas regras.
- conexao.py            abre o arquivo do banco e cria as tabelas.
- cenarios.py           os 10 ingredientes de exemplo e o resultado esperado.
- povoar.py             grava os cenários no banco (com 28 dias de vendas).
- repositorio_sqlite.py RepositorioSQLite: lê o banco e monta os Ingredientes.
"""
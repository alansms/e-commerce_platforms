# e-commerce_platforms

Sistema de Gestão de Estoque e Vendas

Alan de Souza Maximiano - RM557088

André Rovai Jr - RM555848

Pedro Henrique Conte - RM554987

Lancelot Chagas - RM554707

Kauan Alves - RM555082

#Sistema de Gerenciamento de Estoque e Vendas com Flask

Este projeto é uma aplicação web desenvolvida em Flask para gerenciar produtos e vendas. Inclui autenticação de usuários, adição e edição de produtos, venda de produtos com geração de recibos em PDF, e fechamento de caixa. A aplicação utiliza o SQLite como banco de dados e possui uma interface amigável para a gestão de um pequeno estoque. Abaixo estão as principais funcionalidades do sistema:

Funcionalidades

1. Autenticação de Usuários

	•	Registro: Permite a criação de novos usuários, com verificação de senhas e confirmação de e-mail.
	•	Login/Logout: Implementa login com hashing de senha seguro e funcionalidade de logout.
	•	Proteção de Rotas: Uso de @login_required para proteger páginas que exigem autenticação.

2. Gerenciamento de Produtos

	•	Adicionar Produtos: O administrador pode adicionar novos produtos ao sistema, especificando nome, código, descrição, quantidade, preço, desconto, estoque mínimo, categoria e marca.
	•	Editar Produtos: Permite editar informações de produtos já cadastrados, como nome, preço e desconto.
	•	Visualizar Produtos: Uma página exibe todos os produtos cadastrados e suas informações detalhadas.

3. Vendas

	•	Descontos e Promoções: O sistema permite aplicar descontos manuais ou promoções a produtos, com o desconto sendo aplicado automaticamente ao valor final.
	•	Emissão de Recibo: Após a venda, é gerado automaticamente um recibo em formato PDF, contendo detalhes como o nome do produto, quantidade, valor unitário com desconto e o total da compra.
	•	Atualização Automática do Estoque: Ao registrar uma venda, a quantidade em estoque do produto é automaticamente reduzida, evitando inconsistências.
	•	Registro de Vendas: Todas as vendas são registradas no banco de dados, permitindo o rastreamento de produtos vendidos e valores.

4. Relatórios

	•	Relatório de Vendas: O sistema gera relatórios detalhados das vendas realizadas, contendo informações como a data da venda, produtos vendidos, quantidade e o valor total arrecadado.
	•	Relatório de Estoque: Exibe a quantidade atual de todos os produtos em estoque, ajudando a monitorar quando é necessário repor os itens.
	•	Histórico de Movimentações: Registro de todas as adições e remoções de estoque, incluindo vendas e atualizações manuais, para fornecer uma visão detalhada das movimentações do inventário.

5. Fechamento de Caixa

	•	Zerar Estoques: Permite fechar o caixa ao final de um período, zerando as quantidades em estoque ou outro atributo conforme necessidade.

Tecnologias Utilizadas

	•	Flask: Framework web usado para criar a API e a interface da aplicação.
	•	Flask-SQLAlchemy: Biblioteca ORM usada para integração com o banco de dados SQLite.
	•	Werkzeug Security: Usada para hashing de senha seguro e verificação de login.
	•	ReportLab: Biblioteca para geração de PDFs, usada para criar recibos de vendas.
	•	HTML + CSS: Frontend básico usando templates Jinja para renderizar as páginas.

Como Rodar o Projeto

	1.	Clone o repositório:
git clone https://github.com/alansms/seu-repositorio.git

	2.	Instale as dependências:
pip install -r requirements.txt

	3.	Inicialize o banco de dados:

flask shell
db.create_all()
exit

	4.	Execute o servidor Flask:

python app.py

Acesse a aplicação em http://localhost:9081.

Estrutura de Diretórios

├── app.py                # Arquivo principal com a aplicação Flask
├── templates/            # Diretório contendo os templates HTML
│   ├── login.html
│   ├── register.html
│   ├── vender_produto.html
│   ├── produtos.html
│   ├── editar_produto.html
│   ├── vendas-2.html
│   └── index.html
├── instance/
│   └── produtos.db       # Banco de dados SQLite
├── requirements.txt       # Arquivo com dependências do projeto


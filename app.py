# Importações principais do Flask e bibliotecas auxiliares
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import locale
import io
from reportlab.pdfgen import canvas  # Para geração de PDFs
import secrets

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
caminho_db = os.path.join(os.path.dirname(__file__), 'instance', 'produtos.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{caminho_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)
db = SQLAlchemy(app)

# Configura o locale para o Brasil (formatação de números e moedas)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    pass

# Definição dos modelos (classes ORM que representam as tabelas do banco de dados)
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(120))
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    valor_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, nullable=True, default=0.0)  # Desconto em porcentagem
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50))
    marca = db.Column(db.String(50))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    data_venda = db.Column(db.DateTime, default=db.func.current_timestamp())
    produto = db.relationship('Produto', backref=db.backref('sales', lazy=True))


class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    tipo_movimentacao = db.Column(db.String(10))  # 'entrada' ou 'saida'
    quantidade = db.Column(db.Integer, nullable=False)
    data_movimentacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    produto = db.relationship('Produto', backref=db.backref('movimentacoes', lazy=True))


# Decorador para garantir que o usuário esteja logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Rota de login de usuário
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('E-mail ou senha inválidos.', 'danger')

    return render_template('login.html')


# Rota de registro de usuário
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('E-mail já registrado.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        novo_usuario = User(nome=nome, email=email, password=hashed_password)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Função para gerar recibo de venda em PDF
def gerar_recibo(produto_nome, quantidade, valor_unitario):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Recibo de Venda")
    p.drawString(100, 700, f"Produto: {produto_nome}")
    p.drawString(100, 650, f"Quantidade: {quantidade}")
    p.drawString(100, 600, f"Valor Unitário com Desconto: R$ {valor_unitario:.2f}")
    total = quantidade * valor_unitario
    p.drawString(100, 550, f"Total: R$ {total:.2f}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='recibo_venda.pdf', mimetype='application/pdf')


# Rota para realizar a venda de produtos
@app.route('/vender_produto', methods=['GET', 'POST'])
@login_required
def vender_produto():
    produtos = Produto.query.all()
    if request.method == 'POST':
        produto_id = request.form['produto']
        quantidade_vendida = int(request.form['quantidade'])
        desconto_manual = float(request.form.get('desconto', 0.0)) / 100
        produto = Produto.query.get(produto_id)
        if produto and produto.quantidade >= quantidade_vendida:
            valor_com_desconto = produto.valor_unitario * (1 - desconto_manual)
            produto.quantidade -= quantidade_vendida
            db.session.commit()
            # Registrar a venda
            nova_venda = Sale(produto_id=produto.id, quantidade=quantidade_vendida, valor_unitario=valor_com_desconto)
            db.session.add(nova_venda)
            db.session.commit()
            # Registrar a movimentação no estoque
            movimentacao = MovimentacaoEstoque(produto_id=produto.id, tipo_movimentacao='saida', quantidade=quantidade_vendida)
            db.session.add(movimentacao)
            db.session.commit()

            return gerar_recibo(produto.nome, quantidade_vendida, valor_com_desconto)
        else:
            flash('Quantidade vendida maior que a disponível em estoque.', 'danger')

    return render_template('vender_produto.html', produtos=produtos)


# Rota para visualizar e adicionar produtos
@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'POST':
        nome = request.form['nome']
        codigo = request.form['codigo']
        descricao = request.form.get('descricao', '')
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])
        desconto = float(request.form.get('desconto', 0.0))
        estoque_minimo = int(request.form.get('estoque_minimo', 0))
        categoria = request.form.get('categoria', '')
        marca = request.form.get('marca', '')
        novo_produto = Produto(nome=nome, codigo=codigo, descricao=descricao, quantidade=quantidade,
                               valor_unitario=preco, desconto=desconto, estoque_minimo=estoque_minimo,
                               categoria=categoria, marca=marca)
        db.session.add(novo_produto)
        db.session.commit()

        # Registrar a movimentação no estoque
        movimentacao = MovimentacaoEstoque(produto_id=novo_produto.id, tipo_movimentacao='entrada', quantidade=quantidade)
        db.session.add(movimentacao)
        db.session.commit()

        flash('Novo produto adicionado com sucesso!', 'success')

    produtos = Produto.query.all()
    return render_template('produtos.html', produtos=produtos)


# Rota para editar produto
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.codigo = request.form['codigo']
        produto.descricao = request.form.get('descricao', produto.descricao)
        produto.quantidade = int(request.form['quantidade'])
        produto.valor_unitario = float(request.form['preco'])
        produto.desconto = float(request.form.get('desconto', produto.desconto))
        produto.estoque_minimo = int(request.form.get('estoque_minimo', produto.estoque_minimo))
        produto.categoria = request.form.get('categoria', produto.categoria)
        produto.marca = request.form.get('marca', produto.marca)

        db.session.commit()

        # Registrar a movimentação no estoque
        movimentacao = MovimentacaoEstoque(produto_id=produto.id, tipo_movimentacao='entrada', quantidade=produto.quantidade)
        db.session.add(movimentacao)
        db.session.commit()

        flash(f'Produto {produto.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('produtos'))

    return render_template('editar_produto.html', produto=produto)


# Rota para visualizar vendas
@app.route('/vendas', methods=['GET'])
@login_required
def vendas():
    produtos = Produto.query.all()
    produto_selecionado = request.args.get('produto_id')

    if produto_selecionado:
        vendas_filtradas = Sale.query.filter_by(produto_id=produto_selecionado).all()
    else:
        vendas_filtradas = Sale.query.all()

    # Calculando o total de vendas
    total = sum(venda.quantidade * venda.valor_unitario for venda in vendas_filtradas)
    total_formatado = locale.currency(total, grouping=True)

    return render_template('vendas-2.html', vendas=vendas_filtradas, total_formatado=total_formatado, produtos=produtos, produto_selecionado=int(produto_selecionado) if produto_selecionado else None)


# Rota para gerar relatório de vendas
@app.route('/relatorio_vendas', methods=['GET'])
@login_required
def relatorio_vendas():
    vendas = Sale.query.all()
    relatorio = []
    total_vendas = 0
    for venda in vendas:
        total_venda = venda.quantidade * venda.valor_unitario
        total_vendas += total_venda  # Acumulando o total de vendas
        relatorio.append({
            'produto': venda.produto.nome,
            'quantidade': venda.quantidade,
            'valor_unitario': venda.valor_unitario,
            'data_venda': venda.data_venda,
            'total_venda': total_venda
        })

    total_vendas_formatado = locale.currency(total_vendas, grouping=True)

    return render_template('relatorio_vendas.html', relatorio=relatorio, total_vendas=total_vendas_formatado)


    return render_template('relatorio_vendas.html', relatorio=relatorio, total_vendas=total_vendas_formatado)


def gerar_pdf_vendas(relatorio, total_vendas):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    # Título
    p.drawString(100, 750, "Relatório de Vendas")

    # Cabeçalho da tabela
    y = 720
    p.drawString(100, y, "Data")
    p.drawString(200, y, "Produto")
    p.drawString(300, y, "Quantidade")
    p.drawString(400, y, "Valor Unitário")
    p.drawString(500, y, "Total")

    # Conteúdo da tabela
    y -= 20
    for item in relatorio:
        p.drawString(100, y, item['data_venda'].strftime('%d/%m/%Y %H:%M'))
        p.drawString(200, y, item['produto'])
        p.drawString(300, y, str(item['quantidade']))
        p.drawString(400, y, f"R$ {item['valor_unitario']:.2f}")
        p.drawString(500, y, f"R$ {item['total_venda']:.2f}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    # Total de Vendas
    p.drawString(100, y, f"Total das Vendas: {total_vendas}")

    # Finalizar o PDF
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer


# Rota para gerar relatório de estoque
@app.route('/relatorio_estoque', methods=['GET'])
@login_required
def relatorio_estoque():
    produtos = Produto.query.all()
    return render_template('relatorio_estoque.html', produtos=produtos)


# Rota para visualizar o histórico de movimentações de estoque
@app.route('/historico_movimentacoes', methods=['GET'])
@login_required
def historico_movimentacoes():
    movimentacoes = MovimentacaoEstoque.query.all()
    return render_template('historico_movimentacoes.html', movimentacoes=movimentacoes)


@app.route('/download_relatorio_vendas')
@login_required
def download_relatorio_vendas():
    vendas = Sale.query.all()
    relatorio = []
    total_vendas = 0
    for venda in vendas:
        total_venda = venda.quantidade * venda.valor_unitario
        total_vendas += total_venda
        relatorio.append({
            'produto': venda.produto.nome,
            'quantidade': venda.quantidade,
            'valor_unitario': venda.valor_unitario,
            'data_venda': venda.data_venda,
            'total_venda': total_venda
        })

    total_vendas_formatado = locale.currency(total_vendas, grouping=True)
    pdf_buffer = gerar_pdf_vendas(relatorio, total_vendas_formatado)

    return send_file(pdf_buffer, as_attachment=True, download_name='relatorio_vendas.pdf', mimetype='application/pdf')


# Rota para fechar o caixa
@app.route('/fechar_caixa', methods=['POST'])
@login_required
def fechar_caixa():
    try:
        # Lógica para fechar o caixa (exemplo: zerar vendas ou atualizar estoque)
        produtos = Produto.query.all()
        for produto in produtos:
            produto.quantidade = 0  # Exemplo de ação ao fechar o caixa (zerar o estoque)

        db.session.commit()
        flash('Caixa fechado com sucesso! As vendas foram zeradas.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao fechar o caixa: {str(e)}', 'danger')

    return redirect(url_for('vendas'))


# Rota para logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('login'))


# Rota para a página inicial (index)
@app.route('/')
@login_required
def index():
    return render_template('index.html')


# Inicializar o banco de dados ao iniciar o servidor
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Certifica que as tabelas no banco de dados estão criadas
    app.run(debug=True, port=9081)
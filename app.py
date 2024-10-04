# Importa a classe Flask para criar a aplicação web,
# render_template para carregar templates HTML,
# request para acessar dados enviados pelo formulário,
# redirect para redirecionar o usuário para outra rota,
# url_for para construir URLs dinamicamente,
# flash para exibir mensagens flash na interface,
# session para gerenciar sessões de usuário,
# e send_file para enviar arquivos (neste caso, PDFs) para download.
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file

# Importa funções de segurança da biblioteca Werkzeug:
# generate_password_hash é usado para criar senhas com hash,
# check_password_hash para verificar senhas com hash.
from werkzeug.security import generate_password_hash, check_password_hash

# SQLAlchemy é a biblioteca de ORM (Object Relational Mapping) que permite trabalhar
# com banco de dados usando classes e objetos em vez de SQL diretamente.
# SQLAlchemy facilita a interação com o banco de dados.
from flask_sqlalchemy import SQLAlchemy

# wraps é uma função do módulo functools que preserva informações importantes
# ao criar decorators personalizados (por exemplo, o decorator de login_required).
from functools import wraps

# Importa os módulos os e locale.
# 'os' é utilizado para interagir com o sistema de arquivos,
# por exemplo, para construir caminhos de arquivos corretamente.
# 'locale' é usado para configurar as opções regionais, como a formatação de números e moedas.
import os
import locale
import io  # Para gerar PDFs
from reportlab.pdfgen import canvas  # Biblioteca para geração de PDFs

app = Flask(__name__)

# Configuração do banco de dados SQLite
caminho_db = os.path.join(os.path.dirname(__file__), 'instance', 'produtos.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{caminho_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua_chave_secreta_aqui'
db = SQLAlchemy(app)

# Configurar locale para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Modelos (Tabelas)
# Modelo de Produto
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

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Modelo de Venda (Histórico de vendas)
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    data_venda = db.Column(db.DateTime, default=db.func.current_timestamp())
    produto = db.relationship('Produto', backref=db.backref('sales', lazy=True))

# Função para garantir que o usuário esteja logado
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

        user_exist = User.query.filter_by(email=email).first()
        if user_exist:
            flash('E-mail já registrado.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        novo_usuario = User(nome=nome, email=email, password=hashed_password)
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Agora você pode fazer login.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar usuário: {str(e)}', 'danger')

        return redirect(url_for('login'))

    return render_template('register.html')

# Função para gerar recibo em PDF
def gerar_recibo(produto_nome, quantidade, valor_unitario):
    if not produto_nome or quantidade <= 0 or valor_unitario <= 0:
        flash('Erro na geração do recibo: dados inválidos.', 'danger')
        return redirect(url_for('vender_produto'))

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
        try:
            produto_id = request.form['produto']
            quantidade_vendida = int(request.form['quantidade'])
            desconto_manual = float(request.form.get('desconto', 0.0)) / 100
            produto = Produto.query.get(produto_id)
            if produto and produto.quantidade >= quantidade_vendida:
                valor_com_desconto = produto.valor_unitario * (1 - desconto_manual)
                produto.quantidade -= quantidade_vendida
                db.session.commit()
                return gerar_recibo(produto.nome, quantidade_vendida, valor_com_desconto)
            else:
                flash('Quantidade vendida maior que a disponível em estoque.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao realizar venda: {str(e)}', 'danger')
        return redirect(url_for('vender_produto'))
    return render_template('vender_produto.html', produtos=produtos)

# Rota para visualizar e adicionar produtos
@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'POST':
        try:
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
            flash('Novo produto adicionado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar o produto: {str(e)}', 'danger')
    produtos = Produto.query.all()
    return render_template('produtos.html', produtos=produtos)

# Rota para editar produto
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    if request.method == 'POST':
        try:
            produto.nome = request.form['novo_nome']
            produto.valor_unitario = float(request.form['novo_preco'])
            produto.desconto = float(request.form.get('novo_desconto', produto.desconto))
            db.session.commit()
            flash(f'Produto {produto.nome} atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o produto: {str(e)}', 'danger')
        return redirect(url_for('produtos'))
    return render_template('editar_produto.html', produto=produto)

# Rota para fechar o caixa
@app.route('/fechar_caixa', methods=['POST'])
@login_required
def fechar_caixa():
    try:
        produtos = Produto.query.all()
        for produto in produtos:
            produto.quantidade = 0
        db.session.commit()
        flash('Caixa fechado com sucesso! As vendas foram zeradas.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao fechar o caixa: {str(e)}', 'danger')

    return redirect(url_for('vendas'))

# Rota para visualizar vendas

@ app.route('/vendas', methods=['GET'])
@ login_required
def vendas():
    produtos = Produto.query.all()
    produto_filtrado_id = request.args.get('produto')

    # Filtrar vendas com base no produto selecionado
    if produto_filtrado_id:
        produto_selecionado = Produto.query.get(produto_filtrado_id)
        vendas_filtradas = [produto_selecionado] if produto_selecionado else []
    else:
        vendas_filtradas = Produto.query.all()

    # Cálculo do total de vendas
    total = sum(produto.valor_unitario * produto.quantidade for produto in vendas_filtradas)
    total_formatado = locale.currency(total, grouping=True)

    return render_template('vendas-2.html', vendas=vendas_filtradas, total=total_formatado, produtos=produtos,
                           produto_selecionado=produto_filtrado_id)


# Rota para relatório de vendas
@app.route('/relatorio_vendas')
@login_required
def relatorio_vendas():
    vendas = Sale.query.all()
    total_vendas = sum(venda.quantidade * venda.valor_unitario for venda in vendas)
    return render_template('relatorio_vendas.html', vendas=vendas, total_vendas=total_vendas)


# Rota para relatório de estoque
@app.route('/relatorio_estoque')
@login_required
def relatorio_estoque():
    produtos = Produto.query.all()
    return render_template('relatorio_estoque.html', produtos=produtos)


# Rota para adicionar responsável (exemplo de funcionalidade extra)
@app.route('/adicionar_responsavel', methods=['POST'])
@login_required
def adicionar_responsavel():
    nome = request.form['nome']
    flash(f'Responsável {nome} adicionado com sucesso!', 'success')
    return redirect(url_for('painel_principal'))


# Rota para a página inicial (index)
@app.route('/index')
@login_required
def index():
    return render_template('index.html')


# Rota para logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('login'))


# Rota para a página inicial (home)
@app.route('/')
@login_required
def home():
    return redirect(url_for('index'))


# Inicializar o banco de dados ao iniciar o servidor
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9081)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Configuração do banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'produtos.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Modelo para a tabela 'Produto'
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    valor_unitario = db.Column(db.Float, nullable=False, default=0.0)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(100), nullable=True)
    marca = db.Column(db.String(100), nullable=True)
    caracteristica = db.Column(db.String(100), nullable=True)
    desconto = db.Column(db.Float, nullable=True, default=0.0)  # Campo de desconto

    def aplicar_desconto(self, porcentagem):
        if porcentagem < 0 or porcentagem > 100:
            raise ValueError("Porcentagem de desconto inválida.")
        self.desconto = porcentagem

    def __repr__(self):
        return f'<Produto {self.nome}>'


# Modelo para a tabela 'User'
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        # Use e.g., werkzeug.security.generate_password_hash para hashear senhas
        self.password = password

    def check_password(self, password):
        # Use e.g., werkzeug.security.check_password_hash para verificar senhas
        return self.password == password

    def __repr__(self):
        return f'<User {self.nome}>'


if __name__ == "__main__":
    # Criar o banco de dados se não existir
    with app.app_context():
        db.create_all()  # Certifica que o banco de dados e tabelas são criados
    app.run(debug=True, port=7001)

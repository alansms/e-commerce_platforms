from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
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
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    estoque_minimo = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(100), nullable=True)
    marca = db.Column(db.String(100), nullable=True)
    caracteristica = db.Column(db.String(100), nullable=True)
    desconto = db.Column(db.Float, nullable=True, default=0.0)  # Campo de desconto

    def __repr__(self):
        return f'<Produto {self.nome}>'

# Modelo para a tabela 'User'
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.nome}>'

if __name__ == "__main__":
    # Executar o aplicativo
    app.run(debug=True, port=1001)
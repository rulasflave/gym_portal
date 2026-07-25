from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    print(f'Total clientes: {Cliente.query.count()}')

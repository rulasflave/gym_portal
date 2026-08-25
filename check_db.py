from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    total = Cliente.query.count()
    print(f'Total: {total}')

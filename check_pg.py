from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    print(f'DB URI: {app.config["SQLALCHEMY_DATABASE_URI"][:50]}...')
    db.create_all()
    total = Cliente.query.count()
    print(f'Total clients in PostgreSQL: {total}')

from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    print(f'Total: {len(clientes)}')
    for c in clientes:
        print(f'{c.numero_registro} - {c.nombre_completo} - {c.tipo_membresia} - activo={c.activo}')

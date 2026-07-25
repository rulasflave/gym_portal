from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    cliente = Cliente.query.filter_by(numero_registro='V008').first()
    if cliente:
        print(f'V008 - id_cliente: {cliente.id_cliente}')
        print(f'Nombre: {cliente.nombre_completo}')
    else:
        print('V008 not found')
    
    all_clients = Cliente.query.order_by(Cliente.numero_registro).all()
    for c in all_clients:
        print(f'{c.numero_registro} -> id={c.id_cliente}')

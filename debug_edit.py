from app import create_app
from extensions import db
from models.cliente import Cliente
from models.admin import Admin
from werkzeug.security import check_password_hash

app = create_app()
with app.app_context():
    admin = Admin.query.filter_by(email='admin@gym.com').first()
    print(f'Admin found: {admin is not None}, id={admin.id_admin if admin else None}')
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = admin.get_id()
        
        resp = client.get('/admin/clientes/6/editar')
        print(f'/admin/clientes/6/editar -> status: {resp.status_code}')
        
        resp = client.get('/admin/clientes/4/editar')
        print(f'/admin/clientes/4/editar -> status: {resp.status_code}')
        
        cliente6 = Cliente.query.get(6)
        print(f'Cliente id=6 exists: {cliente6 is not None}, nombre: {cliente6.nombre_completo if cliente6 else "N/A"}')
        
        cliente4 = Cliente.query.get(4)
        print(f'Cliente id=4 exists: {cliente4 is not None}, nombre: {cliente4.nombre_completo if cliente4 else "N/A"}')

from app import create_app
from extensions import db
from models.cliente import Cliente

app = create_app()
with app.app_context():
    total = Cliente.query.count()
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    print(f'Total in DB: {total}')
    print(f'Query returns: {len(clientes)}')
    
    for c in clientes[:5]:
        print(f'  {c.numero_registro} - {c.nombre_completo} - tipo={c.tipo_membresia} - fin={c.fecha_fin_membresia} - activo={c.activo}')
    
    print('...')
    
    with app.test_client() as client:
        from werkzeug.security import generate_password_hash
        from models.admin import Admin
        admin = Admin.query.filter_by(email='admin@gym.com').first()
        if admin:
            with client.session_transaction() as sess:
                sess['_user_id'] = admin.get_id()
            resp = client.get('/admin/clientes')
            html = resp.data.decode()
            rows = html.count('<tr>')
            print(f'\nHTTP response status: {resp.status_code}')
            print(f'Table rows in HTML: {rows}')
            if 'V008' in html:
                print('V008 found in HTML')
            else:
                print('V008 NOT found in HTML')
            if 'V049' in html:
                print('V049 found in HTML')
            else:
                print('V049 NOT found in HTML')

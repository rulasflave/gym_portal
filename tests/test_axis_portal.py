from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente


def _login(app, client, num='A001', nombre='Axis User', empresa='Axis'):
    with app.app_context():
        inicio = date.today() - timedelta(days=30)
        fin = date.today() + timedelta(days=300)
        c = Cliente(
            numero_registro=num, nombre_completo=nombre, usuario_login=num,
            password_hash=generate_password_hash('test123'), primer_login=False,
            tipo_membresia='Premium', fecha_inicio_membresia=inicio,
            fecha_fin_membresia=fin, empresa=empresa,
        )
        db.session.add(c)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': num, 'password': 'test123'})


def test_axis_dashboard_requiere_login(client):
    resp = client.get('/ax/portal/dashboard', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Iniciar Sesi' in resp.data


def test_axis_dashboard_carga_para_cliente_axis(app, client):
    _login(app, client)
    resp = client.get('/ax/portal/dashboard')
    assert resp.status_code == 200
    data = resp.data
    assert b'Entrenamiento' in data
    assert b'axis-hybrid-logo' in data
    assert b'dashboard_axis.css' in data
    assert b'AXIS HYBRID' in data


def test_axis_dashboard_bloquea_box(app, client):
    _login(app, client, num='B001', nombre='Box User', empresa='Box')
    resp = client.get('/ax/portal/dashboard')
    assert resp.status_code == 404


def test_login_cliente_box_redirige_a_portal_vitelas(app, client):
    _login(app, client, num='BX1', nombre='Box Auth', empresa='Box')
    resp = client.post('/vitelas/login', data={'usuario': 'BX1', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/vitelas/portal/dashboard')


def test_axis_cliente_bloqueado_en_portal_vitelas(app, client):
    _login(app, client, num='AX9', nombre='Axis Bloqueado', empresa='Axis')
    resp = client.get('/vitelas/portal/dashboard')
    assert resp.status_code == 404
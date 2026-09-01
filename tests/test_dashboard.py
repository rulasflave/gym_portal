from datetime import date
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente


def _login_dashboard(app, client, num='V900', nombre='Dash User'):
    with app.app_context():
        cliente = Cliente(
            numero_registro=num,
            nombre_completo=nombre,
            usuario_login=num,
            password_hash=generate_password_hash('test123'),
            primer_login=False,
            tipo_membresia='Premium',
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31),
            empresa='Box',
        )
        db.session.add(cliente)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': num, 'password': 'test123'})
    return cliente


def test_dashboard_resumen_loads(app, client):
    _login_dashboard(app, client)
    resp = client.get('/vitelas/portal/dashboard')
    assert resp.status_code == 200
    # Tarjeta membresía + marcadores clave del Resumen
    assert b'MEMBRES' in resp.data
    assert b'Powered by' in resp.data


def test_dashboard_shows_user_name(app, client):
    _login_dashboard(app, client, num='V901', nombre='Carla Perez')
    resp = client.get('/vitelas/portal/dashboard')
    assert resp.status_code == 200
    assert b'Carla Perez' in resp.data


def test_perfil_modal_present(app, client):
    _login_dashboard(app, client, num='V902', nombre='Perfil User')
    resp = client.get('/vitelas/portal/dashboard')
    assert b'Mi Perfil' in resp.data
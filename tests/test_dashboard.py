from datetime import date, timedelta, datetime
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente
from models.asistencia import Asistencia
from models.noticia import Noticia


def _login_dashboard(app, client, num='V900', nombre='Dash User'):
    with app.app_context():
        inicio = date.today() - timedelta(days=30)
        fin = date.today() + timedelta(days=300)
        cliente = Cliente(
            numero_registro=num,
            nombre_completo=nombre,
            usuario_login=num,
            password_hash=generate_password_hash('test123'),
            primer_login=False,
            tipo_membresia='Premium',
            fecha_inicio_membresia=inicio,
            fecha_fin_membresia=fin,
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


def test_dashboard_counts_month_attendance(app, client):
    _login_dashboard(app, client, num='V903')
    now = datetime.now()
    with app.app_context():
        c = Cliente.query.filter_by(numero_registro='V903').first()
        db.session.add(Asistencia(id_cliente=c.id_cliente, fecha_hora_entrada=now))
        db.session.add(Asistencia(id_cliente=c.id_cliente, fecha_hora_entrada=now))
        db.session.commit()
    resp = client.get('/vitelas/portal/dashboard')
    assert b'>2</span>' in resp.data


def test_secondary_pages_use_dark_layout(app, client):
    _login_dashboard(app, client, num='V904')
    for path in ['/vitelas/portal/mi-qr', '/vitelas/portal/asistencias',
                 '/vitelas/portal/pagos', '/vitelas/portal/noticias',
                 '/vitelas/portal/cambiar-password']:
        r = client.get(path)
        assert r.status_code == 200, path
        assert b'Vitellas Hub' in r.data, path


def test_dashboard_excludes_prior_month_attendance(app, client):
    _login_dashboard(app, client, num='V905')
    with app.app_context():
        c = Cliente.query.filter_by(numero_registro='V905').first()
        db.session.add(Asistencia(id_cliente=c.id_cliente,
                                  fecha_hora_entrada=datetime.now() - timedelta(days=45)))
        db.session.commit()
    resp = client.get('/vitelas/portal/dashboard')
    assert b'>0</span>' in resp.data
    assert b'0% del objetivo' in resp.data


def test_dashboard_shows_empresa_org_card(app, client):
    _login_dashboard(app, client, num='V906', nombre='Axis User')
    with app.app_context():
        c = Cliente.query.filter_by(numero_registro='V906').first()
        c.empresa = 'Axis'
        db.session.commit()
    resp = client.get('/vitelas/portal/dashboard')
    assert resp.status_code == 200
    assert b'Axis' in resp.data
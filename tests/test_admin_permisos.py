from extensions import db
from werkzeug.security import generate_password_hash
from models.admin import Admin


def _crear(app, rol='admin', permisos=None, email='adm@test.com', password='pw', activo=True):
    with app.app_context():
        db.session.add(Admin(nombre='A', email=email,
                             password_hash=generate_password_hash(password),
                             rol=rol, permisos=permisos, activo=activo))
        db.session.commit()


def _login(client, email, password='pw'):
    return client.post('/vitelas/login', data={'usuario': email, 'password': password})


def test_super_accede_a_todas_las_secciones(app, client):
    _crear(app, rol='superadmin', email='sup@test.com')
    _login(client, 'sup@test.com')
    for url in ['/vitelas/admin/dashboard', '/vitelas/admin/clientes',
                '/vitelas/admin/pagos', '/vitelas/admin/noticias',
                '/vitelas/admin/mensajes', '/vitelas/admin/solicitudes',
                '/vitelas/admin/reportes',
                '/vitelas/admin/configuracion-recordatorios']:
        assert client.get(url).status_code == 200, url


def test_restringido_accede_a_seccion_permitida(app, client):
    _crear(app, permisos='clientes', email='res@test.com')
    _login(client, 'res@test.com')
    assert client.get('/vitelas/admin/clientes').status_code == 200


def test_restringido_403_en_seccion_no_permitida(app, client):
    _crear(app, permisos='clientes', email='res2@test.com')
    _login(client, 'res2@test.com')
    assert client.get('/vitelas/admin/pagos').status_code == 403
    assert client.get('/vitelas/admin/mensajes').status_code == 403
    assert client.get('/vitelas/admin/configuracion-recordatorios').status_code == 403


def test_restringido_403_en_subaccion_no_permitida(app, client):
    _crear(app, permisos='pagos', email='res3@test.com')
    _login(client, 'res3@test.com')
    assert client.get('/vitelas/admin/clientes/nuevo').status_code == 403

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


def test_super_ve_administradores(app, client):
    _crear(app, rol='superadmin', email='sup@test.com')
    _login(client, 'sup@test.com')
    assert client.get('/vitelas/admin/administradores').status_code == 200


def test_restringido_403_en_administradores(app, client):
    _crear(app, permisos='clientes', email='res4@test.com')
    _login(client, 'res4@test.com')
    assert client.get('/vitelas/admin/administradores').status_code == 403
    assert client.post('/vitelas/admin/administradores/nuevo', data={}).status_code == 403


def test_crear_admin_desde_ui(app, client):
    _crear(app, rol='superadmin', email='sup2@test.com')
    _login(client, 'sup2@test.com')
    resp = client.post('/vitelas/admin/administradores/nuevo', data={
        'nombre': 'Nuevo', 'email': 'nuevo@test.com', 'password': 'newpass',
        'secciones': ['clientes', 'pagos'], 'activo': 'on'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        a = Admin.query.filter_by(email='nuevo@test.com').first()
        assert a is not None and a.rol == 'admin'
        assert set(a.permisos.split(',')) == {'clientes', 'pagos'}


def test_crear_admin_sin_secciones_no_crea(app, client):
    _crear(app, rol='superadmin', email='sup3@test.com')
    _login(client, 'sup3@test.com')
    client.post('/vitelas/admin/administradores/nuevo', data={
        'nombre': 'X', 'email': 'nosec@test.com', 'password': 'pw',
        'secciones': [], 'activo': 'on'})
    with app.app_context():
        assert Admin.query.filter_by(email='nosec@test.com').first() is None


def test_crear_admin_email_duplicado_no_crea(app, client):
    _crear(app, rol='superadmin', email='sup4@test.com')
    _crear(app, email='dup@test.com', permisos='clientes')
    _login(client, 'sup4@test.com')
    client.post('/vitelas/admin/administradores/nuevo', data={
        'nombre': 'Y', 'email': 'dup@test.com', 'password': 'pw',
        'secciones': ['pagos'], 'activo': 'on'})
    with app.app_context():
        assert Admin.query.filter_by(email='dup@test.com').first().permisos == 'clientes'


def test_desactivar_admin_impide_login(app, client):
    _crear(app, rol='superadmin', email='sup5@test.com')
    _crear(app, email='des@test.com', permisos='clientes')
    _login(client, 'sup5@test.com')
    with app.app_context():
        id_des = Admin.query.filter_by(email='des@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_des}/desactivar')
    client.get('/vitelas/logout')
    assert _login(client, 'des@test.com').status_code == 200


def test_super_no_puede_autodesactivarse(app, client):
    _crear(app, rol='superadmin', email='sup6@test.com')
    _login(client, 'sup6@test.com')
    with app.app_context():
        id_sup = Admin.query.filter_by(email='sup6@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_sup}/desactivar')
    with app.app_context():
        assert Admin.query.get(id_sup).activo is True


def test_reset_password_admin(app, client):
    _crear(app, rol='superadmin', email='sup7@test.com')
    _crear(app, email='rp@test.com', permisos='clientes')
    _login(client, 'sup7@test.com')
    with app.app_context():
        id_rp = Admin.query.filter_by(email='rp@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_rp}/reset-password',
                data={'password': 'brandnew'})
    client.get('/vitelas/logout')
    assert _login(client, 'rp@test.com', 'brandnew').status_code == 302


def test_super_ve_menu_completo(app, client):
    _crear(app, rol='superadmin', email='menusup@test.com')
    _login(client, 'menusup@test.com')
    html = client.get('/vitelas/admin/dashboard').get_data(as_text=True)
    for href in ['/vitelas/admin/dashboard', '/vitelas/admin/clientes',
                 '/vitelas/admin/pagos', '/vitelas/admin/noticias',
                 '/vitelas/admin/mensajes', '/vitelas/admin/solicitudes',
                 '/vitelas/admin/reportes',
                 '/vitelas/admin/configuracion-recordatorios',
                 '/vitelas/admin/administradores']:
        assert href in html, href


def test_restringido_ve_solo_su_seccion_en_menu(app, client):
    _crear(app, permisos='clientes', email='menures@test.com')
    _login(client, 'menures@test.com')
    html = client.get('/vitelas/admin/clientes').get_data(as_text=True)
    assert '/vitelas/admin/clientes' in html
    assert '/vitelas/admin/pagos' not in html
    assert '/vitelas/admin/configuracion-recordatorios' not in html
    assert '/vitelas/admin/administradores' not in html


def test_editar_admin_cambia_secciones(app, client):
    _crear(app, rol='superadmin', email='supedit@test.com')
    _crear(app, email='edit@test.com', permisos='clientes')
    _login(client, 'supedit@test.com')
    with app.app_context():
        id_e = Admin.query.filter_by(email='edit@test.com').first().id_admin
    resp = client.post(f'/vitelas/admin/administradores/{id_e}/editar', data={
        'nombre': 'Edit', 'email': 'edit@test.com',
        'secciones': ['pagos', 'noticias'], 'activo': 'on'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert set(Admin.query.get(id_e).permisos.split(',')) == {'pagos', 'noticias'}


def test_editar_admin_sin_secciones_no_cambia(app, client):
    _crear(app, rol='superadmin', email='supedit2@test.com')
    _crear(app, email='edit2@test.com', permisos='clientes')
    _login(client, 'supedit2@test.com')
    with app.app_context():
        id_e = Admin.query.filter_by(email='edit2@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_e}/editar', data={
        'nombre': 'Edit', 'email': 'edit2@test.com',
        'secciones': [], 'activo': 'on'})
    with app.app_context():
        assert Admin.query.get(id_e).permisos == 'clientes'


def test_activar_admin(app, client):
    _crear(app, rol='superadmin', email='supact@test.com')
    _crear(app, email='act@test.com', permisos='clientes', activo=False)
    _login(client, 'supact@test.com')
    with app.app_context():
        id_a = Admin.query.filter_by(email='act@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_a}/activar')
    with app.app_context():
        assert Admin.query.get(id_a).activo is True


def test_no_se_puede_resetear_ni_activar_al_super(app, client):
    _crear(app, rol='superadmin', email='supself@test.com')
    _login(client, 'supself@test.com')
    with app.app_context():
        id_sup = Admin.query.filter_by(email='supself@test.com').first().id_admin
    client.post(f'/vitelas/admin/administradores/{id_sup}/reset-password', data={'password': 'hacked'})
    client.post(f'/vitelas/admin/administradores/{id_sup}/activar')
    with app.app_context():
        assert Admin.query.get(id_sup).activo is True
    client.get('/vitelas/logout')
    # la contraseña del super no cambió
    assert _login(client, 'supself@test.com', 'pw').status_code == 302


def test_archivo_solicitud_no_accesible_anonimo(client):
    resp = client.get('/vitelas/admin/solicitudes/1/archivo')
    assert resp.status_code != 200
    assert resp.status_code in (302, 403)

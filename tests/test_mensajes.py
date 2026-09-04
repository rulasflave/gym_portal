from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente
from services.mensajeria import crear_mensaje, no_leidos


def _cliente(app, num='V700', nombre='Msg User'):
    with app.app_context():
        c = Cliente(
            numero_registro=num, nombre_completo=nombre, usuario_login=num,
            password_hash=generate_password_hash('test123'), primer_login=False,
        )
        db.session.add(c)
        db.session.commit()
        return c.id_cliente


def test_crear_mensaje_y_no_leidos(app, client):
    cid = _cliente(app)
    with app.app_context():
        crear_mensaje(cid, 'Hola', '<p>Bienvenido</p>')
        db.session.commit()
        assert no_leidos(cid) == 1


def test_marcar_leido_resta_contador(app, client):
    cid = _cliente(app, num='V701')
    with app.app_context():
        m = crear_mensaje(cid, 'Aviso', '<p>Cuerpo</p>')
        db.session.commit()
        m.leido = True
        db.session.commit()
        assert no_leidos(cid) == 0


def test_dash_bandeja_menu_y_badge(app, client):
    cid = _cliente(app, num='V702', nombre='Bandeja User')
    with app.app_context():
        crear_mensaje(cid, 'Aviso', '<p>hola</p>', es_automatico=True)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': 'V702', 'password': 'test123'})
    resp = client.get('/vitelas/portal/dashboard')
    assert b'Bandeja' in resp.data
    assert b'notif-dot' not in resp.data
    assert b'1' in resp.data


def test_bandeja_muestra_mensajes_y_marca_leido(app, client):
    import json as _json
    cid = _cliente(app, num='V703', nombre='Bandeja2')
    with app.app_context():
        from models.mensaje import Mensaje
        m = crear_mensaje(cid, 'Oferta', '<p><b>Texto</b></p>', es_automatico=False)
        db.session.commit()
        mid = m.id_mensaje
    client.post('/vitelas/login', data={'usuario': 'V703', 'password': 'test123'})
    resp = client.get('/vitelas/portal/bandeja')
    assert resp.status_code == 200
    assert b'Oferta' in resp.data
    r2 = client.post(f'/vitelas/portal/bandeja/{mid}/leer')
    assert r2.status_code == 200
    assert _json.loads(r2.data) == {'no_leidos': 0}


def _login_admin(app, client, nombre='Admin', email='admin@test.com'):
    from models.admin import Admin
    from werkzeug.security import generate_password_hash as g
    with app.app_context():
        a = Admin(nombre=nombre, email=email,
                  password_hash=g('adminpass'), rol='admin', activo=True)
        db.session.add(a)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': email, 'password': 'adminpass'})


def test_admin_crea_mensaje(app, client):
    cid = _cliente(app, num='V704')
    _login_admin(app, client)
    with app.app_context():
        from models.mensaje import Mensaje
        r = client.post('/vitelas/admin/mensajes/nuevo', data={
            'id_cliente': str(cid),
            'asunto': 'Bienvenido',
            'cuerpo': '<p><b>Hola</b></p>',
        })
        assert r.status_code in (302, 200)
        m = Mensaje.query.filter_by(id_cliente=cid).first()
        assert m is not None
        assert m.asunto == 'Bienvenido'
        assert m.leido is False
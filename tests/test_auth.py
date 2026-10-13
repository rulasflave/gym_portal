import pytest
from datetime import date
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente


def test_login_page_loads(client):
    response = client.get('/vitelas/login')
    assert response.status_code == 200


def test_login_with_valid_credentials(app, client):
    with app.app_context():
        password_hash = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V001',
            nombre_completo='Test User',
            usuario_login='V001',
            password_hash=password_hash,
            primer_login=False,
            fecha_fin_membresia=date(2026, 8, 1)
        )
        db.session.add(cliente)
        db.session.commit()

    response = client.post('/vitelas/login', data={
        'usuario': 'V001',
        'password': 'test123'
    })
    assert response.status_code == 302


def test_login_with_invalid_credentials(client):
    response = client.post('/vitelas/login', data={
        'usuario': 'invalid',
        'password': 'invalid'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_cliente_axis_redirige_a_portal_axis(app, client):
    with app.app_context():
        c = Cliente(
            numero_registro='AUTH1', nombre_completo='Axis Auth',
            usuario_login='AUTH1', empresa='Axis',
            password_hash=generate_password_hash('test123'), primer_login=False,
        )
        db.session.add(c)
        db.session.commit()
    resp = client.post('/vitelas/login', data={'usuario': 'AUTH1', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/ax/portal/dashboard')


def _admin(activo=True, rol='admin', permisos=None, email='a@a.com', password='pw'):
    from models.admin import Admin
    return Admin(nombre='A', email=email,
                 password_hash=generate_password_hash(password),
                 rol=rol, activo=activo, permisos=permisos)


def test_login_admin_inactivo_rechazado(app, client):
    with app.app_context():
        db.session.add(_admin(activo=False, email='inact@a.com'))
        db.session.commit()
    resp = client.post('/vitelas/login', data={'usuario': 'inact@a.com', 'password': 'pw'})
    # credenciales válidas pero inactivo => NO redirige (se queda en login 200)
    assert resp.status_code == 200


def test_login_super_redirige_dashboard(app, client):
    from flask import url_for
    with app.app_context():
        db.session.add(_admin(rol='superadmin', email='sup@a.com'))
        db.session.commit()
        with app.test_request_context():
            dest = url_for('admin.dashboard')
    resp = client.post('/vitelas/login', data={'usuario': 'sup@a.com', 'password': 'pw'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(dest)


def test_login_admin_restringido_redirige_primera_seccion(app, client):
    from flask import url_for
    with app.app_context():
        db.session.add(_admin(rol='admin', permisos='mensajes', email='res@a.com'))
        db.session.commit()
        with app.test_request_context():
            dest = url_for('admin.mensajes')
    resp = client.post('/vitelas/login', data={'usuario': 'res@a.com', 'password': 'pw'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith(dest)

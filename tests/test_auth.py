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

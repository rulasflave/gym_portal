import pytest
from datetime import date
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente


def test_login_page_loads(client):
    response = client.get('/login')
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

    response = client.post('/login', data={
        'usuario': 'V001',
        'password': 'test123'
    })
    assert response.status_code == 302


def test_login_with_invalid_credentials(client):
    response = client.post('/login', data={
        'usuario': 'invalid',
        'password': 'invalid'
    }, follow_redirects=True)
    assert response.status_code == 200

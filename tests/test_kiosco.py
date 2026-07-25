import pytest
from extensions import db
from models.cliente import Cliente
from werkzeug.security import generate_password_hash
from datetime import date
import json

def test_kiosco_page_loads(client):
    response = client.get('/kiosco/')
    assert response.status_code == 200
    assert 'Check-in' in response.data.decode()

def test_validar_codigo_inexistente(client):
    response = client.post('/kiosco/validar',
        data=json.dumps({'codigo': 'INVALID'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'error'

def test_validar_codigo_cliente_activo(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V001',
            nombre_completo='Test User',
            nickname='Test',
            usuario_login='V001',
            password_hash=password,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()
    
    response = client.post('/kiosco/validar',
        data=json.dumps({'codigo': 'V001'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'Bienvenido' in data['mensaje']

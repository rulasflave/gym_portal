import pytest
from extensions import db
from models.cliente import Cliente
from models.asistencia import Asistencia
from werkzeug.security import generate_password_hash
from datetime import date, timedelta, datetime, timezone
import json


def _crear_cliente(app, numero='V001', fin=None, nacimiento=None, inicio=None):
    with app.app_context():
        if inicio is None:
            inicio = date.today() - timedelta(days=60)
        if fin is None:
            fin = date.today() + timedelta(days=30)
        cliente = Cliente(
            numero_registro=numero,
            nombre_completo='Test User',
            nickname='Test',
            usuario_login=numero,
            password_hash=generate_password_hash('test123'),
            fecha_inicio_membresia=inicio,
            fecha_fin_membresia=fin,
            fecha_nacimiento=nacimiento,
        )
        db.session.add(cliente)
        db.session.commit()
    return numero


def test_kiosco_page_loads(client):
    response = client.get('/vitelas/kiosco/')
    assert response.status_code == 200
    assert 'Ingresa tu código' in response.data.decode()


def test_validar_codigo_inexistente(client):
    response = client.post('/vitelas/kiosco/validar',
        data=json.dumps({'codigo': 'INVALID'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'message' in data


def test_validar_codigo_cliente_activo(app, client):
    _crear_cliente(app, numero='V001')
    response = client.post('/vitelas/kiosco/validar',
        data=json.dumps({'codigo': 'V001'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'Bienvenido' in data['mensaje']
    assert 'foto_url' in data
    assert 'es_cumpleanos' in data
    assert data['grace_period'] is False


def test_validar_cumpleanos(app, client):
    _crear_cliente(app, numero='V002', nacimiento=date.today())
    response = client.post('/vitelas/kiosco/validar',
        data=json.dumps({'codigo': 'V002'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['es_cumpleanos'] is True
    assert 'Feliz cumpleaños' in data['mensaje']


def test_validar_membresia_vencida(app, client):
    _crear_cliente(app, numero='V003', fin=date.today() - timedelta(days=30))
    response = client.post('/vitelas/kiosco/validar',
        data=json.dumps({'codigo': 'V003'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'vencida'
    assert 'venció' in data['message']


def test_validar_dia_gracia(app, client):
    _crear_cliente(app, numero='V004', fin=date.today() - timedelta(days=1))
    response = client.post('/vitelas/kiosco/validar',
        data=json.dumps({'codigo': 'V004'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['grace_period'] is True
    assert data['dias_expirado'] == 1
    assert 'Días de gracia' in data['mensaje']


def test_kiosco_flow_markers(client):
    html = client.get('/vitelas/kiosco/').data.decode()
    assert 'manual-entry' in html
    assert 'result-view' in html
    assert 'validarCodigoSilencioso' not in html
    assert 'confetti-piece' in html
    assert 'logos_nbroken_HUB.svg' in html
    css = client.get('/static/css/kiosk.css').data.decode()
    assert 'kiosk-fall' in css


def _agregar_asistencia(app, numero, dt):
    _crear_cliente(app, numero=numero)
    with app.app_context():
        cliente = Cliente.query.filter_by(numero_registro=numero).one()
        db.session.add(Asistencia(id_cliente=cliente.id_cliente, fecha_hora_entrada=dt))
        db.session.commit()


def test_ultimos_accesos_hora_convertida_a_hora_local(app, client):
    _agregar_asistencia(app, 'V010', datetime(2026, 9, 2, 2, 45, tzinfo=timezone.utc))
    response = client.get('/vitelas/kiosco/ultimos-accesos')
    data = json.loads(response.data)
    assert data[0]['hora'] == '20:45'


def test_ultimos_accesos_hora_naive_tratada_como_utc(app, client):
    _agregar_asistencia(app, 'V011', datetime(2026, 9, 2, 2, 45))
    response = client.get('/vitelas/kiosco/ultimos-accesos')
    data = json.loads(response.data)
    assert data[0]['hora'] == '20:45'
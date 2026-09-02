import pytest
from datetime import date, datetime, timezone
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente
from models.asistencia import Asistencia


def test_dashboard_requires_login(client):
    response = client.get('/portal/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_dashboard_loads_for_logged_in_user(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V001',
            nombre_completo='Test User',
            usuario_login='V001',
            password_hash=password,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()

    client.post('/login', data={
        'usuario': 'V001',
        'password': 'test123'
    })

    response = client.get('/portal/dashboard')
    assert response.status_code == 200
    assert b'Test User' in response.data


def test_perfil_requires_login(client):
    response = client.get('/portal/perfil', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_perfil_loads_for_logged_in_user(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V002',
            nombre_completo='Profile User',
            usuario_login='V002',
            password_hash=password,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()

    client.post('/login', data={
        'usuario': 'V002',
        'password': 'test123'
    })

    response = client.get('/portal/perfil')
    assert response.status_code == 200
    assert b'Profile User' in response.data


def test_asistencias_requires_login(client):
    response = client.get('/portal/asistencias', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_asistencias_hora_en_zona_local(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V010',
            nombre_completo='Tz User',
            usuario_login='V010',
            password_hash=password,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()
        db.session.add(Asistencia(id_cliente=cliente.id_cliente,
                                  fecha_hora_entrada=datetime(2026, 9, 2, 2, 45, tzinfo=timezone.utc)))
        db.session.commit()

    client.post('/vitelas/login', data={
        'usuario': 'V010',
        'password': 'test123'
    })

    response = client.get('/vitelas/portal/asistencias')
    body = response.data.decode()
    assert response.status_code == 200
    assert '08:45 PM' in body
    assert '02:45 AM' not in body
    assert '01/09/2026' in body


def test_pagos_requires_login(client):
    response = client.get('/portal/pagos', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_noticias_requires_login(client):
    response = client.get('/portal/noticias', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_cambiar_password_requires_login(client):
    response = client.get('/portal/cambiar-password', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_cambiar_password_updates_password(app, client):
    with app.app_context():
        password = generate_password_hash('oldpass')
        cliente = Cliente(
            numero_registro='V003',
            nombre_completo='Pass User',
            usuario_login='V003',
            password_hash=password,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()

    client.post('/login', data={
        'usuario': 'V003',
        'password': 'oldpass'
    })

    response = client.post('/portal/cambiar-password', data={
        'nueva_password': 'newpass',
        'confirmar_password': 'newpass'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V003').first()
        from werkzeug.security import check_password_hash
        assert check_password_hash(cliente.password_hash, 'newpass')
        assert cliente.primer_login is False


def test_cambiar_password_mismatch_flash(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        cliente = Cliente(
            numero_registro='V004',
            nombre_completo='Mismatch User',
            usuario_login='V004',
            password_hash=password,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()

    client.post('/login', data={
        'usuario': 'V004',
        'password': 'test123'
    })

    response = client.post('/portal/cambiar-password', data={
        'nueva_password': 'pass1',
        'confirmar_password': 'pass2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'no coinciden' in response.data

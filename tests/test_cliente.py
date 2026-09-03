import pytest
from PIL import Image
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


def _login_cliente(app, client, numero, password='test123'):
    with app.app_context():
        pw = generate_password_hash(password)
        cliente = Cliente(
            numero_registro=numero,
            nombre_completo=numero + ' User',
            usuario_login=numero,
            password_hash=pw,
            primer_login=False,
            fecha_inicio_membresia=date(2026, 1, 1),
            fecha_fin_membresia=date(2026, 12, 31)
        )
        db.session.add(cliente)
        db.session.commit()

    client.post('/vitelas/login', data={
        'usuario': numero,
        'password': password
    })


def test_perfil_actualizar_requiere_login(client):
    response = client.post('/vitelas/portal/perfil/actualizar', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar Sesi' in response.data


def test_perfil_actualizar_guarda_campos(app, client):
    _login_cliente(app, client, 'V100')

    response = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Nuevo Nombre',
        'nickname': 'nuevo_nick',
        'telefono': '555-1234',
        'email': 'cliente@mail.com',
        'fecha_nacimiento': '1990-05-20',
        'contacto_emergencia': 'Ana 555-9999',
        'lesiones_medicas': 'Lesion en rodilla'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Tus datos fueron actualizados' in response.data

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V100').one()
        assert cliente.nombre_completo == 'Nuevo Nombre'
        assert cliente.nickname == 'nuevo_nick'
        assert cliente.telefono == '555-1234'
        assert cliente.email == 'cliente@mail.com'
        assert cliente.fecha_nacimiento == date(1990, 5, 20)
        assert cliente.contacto_emergencia == 'Ana 555-9999'
        assert cliente.lesiones_medicas == 'Lesion en rodilla'


def test_perfil_nombre_vacio_no_guarda(app, client):
    _login_cliente(app, client, 'V101')

    response = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': '   ',
        'nickname': 'x'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'El nombre completo es obligatorio' in response.data

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V101').one()
        assert cliente.nombre_completo == 'V101 User'
        assert cliente.nickname is None


def test_perfil_actualizar_no_cambia_campos_admin(app, client):
    _login_cliente(app, client, 'V102')

    response = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Hacker User',
        'tipo_membresia': 'VIP',
        'fecha_fin_membresia': '2099-12-31'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V102').one()
        assert cliente.nombre_completo == 'Hacker User'
        assert cliente.tipo_membresia != 'VIP'
        assert cliente.fecha_fin_membresia != date(2099, 12, 31)


def _imagen_upload(f1):
    from io import BytesIO
    img = Image.new('RGB', (1200, 900), (200, 40, 40))
    img.save(f1, format='PNG')
    f1.seek(0)
    return (f1, 'foto.png')


def test_perfil_actualizar_foto_uploads(app, client):
    import io
    _login_cliente(app, client, 'V103')

    png = _imagen_upload(io.BytesIO())
    response = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Foto User',
        'foto': png
    }, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V103').one()
        assert cliente.foto_data is not None
        assert cliente.foto_mime == 'image/jpeg'


def test_perfil_foto_redimensiona_y_pesa_menos_al_subir(app, client):
    import io
    _login_cliente(app, client, 'V105')

    original = io.BytesIO()
    Image.new('RGB', (1200, 900), (200, 40, 40)).save(original, format='PNG')
    tamano_original = len(original.getbuffer())
    original.seek(0)

    client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Opt User',
        'foto': (original, 'foto.png')
    }, content_type='multipart/form-data', follow_redirects=True)

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V105').one()
        assert cliente.foto_mime == 'image/jpeg'
        assert len(cliente.foto_data) < tamano_original
        img = Image.open(io.BytesIO(cliente.foto_data))
        assert img.width <= 300 and img.height <= 300
        assert img.format == 'JPEG'


def test_perfil_actualizar_nueva_foto_reemplaza_actual(app, client):
    import io
    _login_cliente(app, client, 'V104')

    r1 = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Con Foto',
        'foto': _imagen_upload(io.BytesIO())
    }, content_type='multipart/form-data', follow_redirects=True)
    assert r1.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V104').one()
        assert cliente.foto_data is not None
        assert cliente.foto_mime == 'image/jpeg'

    r2 = client.post('/vitelas/portal/perfil/actualizar', data={
        'nombre_completo': 'Con Foto',
        'foto': _imagen_upload(io.BytesIO())
    }, content_type='multipart/form-data', follow_redirects=True)
    assert r2.status_code == 200

    with app.app_context():
        cliente = Cliente.query.filter_by(usuario_login='V104').one()
        assert cliente.foto_data is not None
        assert cliente.foto_mime == 'image/jpeg'

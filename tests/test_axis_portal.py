from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente


def _login(app, client, num='A001', nombre='Axis User', empresa='Axis'):
    with app.app_context():
        inicio = date.today() - timedelta(days=30)
        fin = date.today() + timedelta(days=300)
        c = Cliente(
            numero_registro=num, nombre_completo=nombre, usuario_login=num,
            password_hash=generate_password_hash('test123'), primer_login=False,
            tipo_membresia='Premium', fecha_inicio_membresia=inicio,
            fecha_fin_membresia=fin, empresa=empresa,
        )
        db.session.add(c)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': num, 'password': 'test123'})


def test_axis_dashboard_requiere_login(client):
    resp = client.get('/ax/portal/dashboard', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Iniciar Sesi' in resp.data


def test_axis_dashboard_carga_para_cliente_axis(app, client):
    _login(app, client)
    resp = client.get('/ax/portal/dashboard')
    assert resp.status_code == 200
    data = resp.data
    assert b'Entrenamiento' in data
    assert b'axis-hybrid-logo' in data
    assert b'dashboard_axis.css' in data
    assert b'AXIS HYBRID' in data


def test_axis_dashboard_bloquea_box(app, client):
    _login(app, client, num='B001', nombre='Box User', empresa='Box')
    resp = client.get('/ax/portal/dashboard')
    assert resp.status_code == 404


def test_login_cliente_box_redirige_a_portal_vitelas(app, client):
    _login(app, client, num='BX1', nombre='Box Auth', empresa='Box')
    resp = client.post('/vitelas/login', data={'usuario': 'BX1', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/vitelas/portal/dashboard')


def test_axis_cliente_bloqueado_en_portal_vitelas(app, client):
    _login(app, client, num='AX9', nombre='Axis Bloqueado', empresa='Axis')
    resp = client.get('/vitelas/portal/dashboard')
    assert resp.status_code == 404


ENTRENAMIENTO_TEST_DATA = {
    'wod_grace': '3:45', 'wod_filthy50': '18:20', 'wod_fight_gone_bad': '312',
    'wod_murph': '41:00', 'wod_max_pull_ups': '25',
    'wod_fran': '4:12', 'wod_sprint_400m': '1:30', 'wod_helen': '9:15', 'wod_run_5km': '22:40',
    'lift_clean_jerk': '225', 'lift_snatch': '185', 'lift_deadlift': '405',
    'lift_back_squat': '315', 'lift_bench_press': '225', 'lift_overhead_squat': '135',
    'atleta_box': 'AXIS HYBRID', 'atleta_peso': '85', 'atleta_estatura': '1.78',
    'atleta_talla_playera': 'L', 'atleta_tipo_sangre': 'O+',
}


def test_entrenamiento_requiere_axis(app, client):
    _login(app, client, num='B100', nombre='Box TRX', empresa='Box')
    assert client.get('/ax/portal/entrenamiento').status_code == 404


def test_entrenamiento_muestra_secciones_axis(app, client):
    _login(app, client, num='AX100', nombre='Axis TRX', empresa='Axis')
    resp = client.get('/ax/portal/entrenamiento')
    assert resp.status_code == 200
    assert b'BENCHMARK WORKOUTS' in resp.data
    assert b'BENCHMARK LIFTS' in resp.data
    assert b'INFO ATLETA' in resp.data
    assert b'Talla Playera' in resp.data
    assert b'Tipo de sangre' in resp.data


def test_entrenamiento_guarda_y_recupera_campos(app, client):
    _login(app, client, num='AX101', nombre='Axis Save', empresa='Axis')
    r = client.post('/ax/portal/entrenamiento', data=ENTRENAMIENTO_TEST_DATA, follow_redirects=True)
    assert r.status_code == 200
    resp = client.get('/ax/portal/entrenamiento')
    for val in ENTRENAMIENTO_TEST_DATA.values():
        assert val.encode() in resp.data
    with app.app_context():
        c = Cliente.query.filter_by(usuario_login='AX101').one()
        assert c.wod_grace == '3:45'
        assert c.lift_deadlift == '405'
        assert c.atleta_tipo_sangre == 'O+'
        assert c.atleta_talla_playera == 'L'


def test_entrenamiento_vacio_guarda_none(app, client):
    _login(app, client, num='AX102', nombre='Axis Empty', empresa='Axis')
    client.post('/ax/portal/entrenamiento', data={}, follow_redirects=True)
    with app.app_context():
        c = Cliente.query.filter_by(usuario_login='AX102').one()
        assert c.wod_grace is None
        assert c.atleta_peso is None


AXIS_PAGINAS = ['/ax/portal/mi-qr', '/ax/portal/asistencias', '/ax/portal/pagos',
                '/ax/portal/noticias', '/ax/portal/cambiar-password', '/ax/portal/bandeja']


def test_axis_paginas_cargan(app, client):
    _login(app, client, num='AX200', nombre='Axis All', empresa='Axis')
    for path in AXIS_PAGINAS:
        r = client.get(path)
        assert r.status_code == 200, path
        body = r.data.decode()
        assert '/ax/portal/' in body, f'{path} no enlaza rutas axis'
        assert '/vitelas/portal/' not in body, f'{path} enlaza rutas vitelas'


def test_axis_bandeja_leer_y_eliminar(app, client):
    from models.mensaje import Mensaje
    _login(app, client, num='AX201', nombre='Axis Msg', empresa='Axis')
    with app.app_context():
        c = Cliente.query.filter_by(usuario_login='AX201').one()
        m = Mensaje(id_cliente=c.id_cliente, asunto='Hola', cuerpo='Cuerpo')
        db.session.add(m)
        db.session.commit()
        mid = m.id_mensaje
    assert client.post(f'/ax/portal/bandeja/{mid}/leer').status_code == 200
    r = client.get(f'/ax/portal/mensajes/{mid}')
    assert r.status_code == 200
    client.post(f'/ax/portal/mensajes/{mid}/eliminar', follow_redirects=True)


def test_ax_login_page_theme_axis(client):
    resp = client.get('/ax/login')
    assert resp.status_code == 200
    assert b'axis-hybrid-logo' in resp.data
    assert b'axis_login' not in resp.data  # no usa templates vitelas


def test_ax_login_cliente_axis_redirige_a_axis(app, client):
    _login(app, client, num='AXL1', nombre='Axis Login', empresa='Axis')
    resp = client.post('/ax/login', data={'usuario': 'AXL1', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/ax/portal/dashboard')


def test_ax_login_cliente_box_redirige_a_vitelas(app, client):
    _login(app, client, num='BXL1', nombre='Box Login', empresa='Box')
    resp = client.post('/ax/login', data={'usuario': 'BXL1', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/vitelas/portal/dashboard')


def test_ax_login_primer_login_va_a_cambiar_password_axis(app, client):
    with app.app_context():
        c = Cliente(
            numero_registro='AXL2', nombre_completo='Axis First',
            usuario_login='AXL2', password_hash=generate_password_hash('test123'),
            primer_login=True, empresa='Axis',
        )
        db.session.add(c)
        db.session.commit()
    resp = client.post('/ax/login', data={'usuario': 'AXL2', 'password': 'test123'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/ax/portal/cambiar-password')


def test_ax_logout_redirige_a_ax_login(app, client):
    _login(app, client, num='AXL3', nombre='Axis Logout', empresa='Axis')
    client.post('/ax/login', data={'usuario': 'AXL3', 'password': 'test123'})
    resp = client.get('/ax/logout')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/ax/login')
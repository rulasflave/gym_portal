import json
import base64
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente
from models.solicitud_validacion import SolicitudValidacion


def _cliente(app, num='V600', nombre='Sol User'):
    with app.app_context():
        c = Cliente(
            numero_registro=num,
            nombre_completo=nombre,
            usuario_login=num,
            password_hash=generate_password_hash('test123'),
            primer_login=False,
        )
        db.session.add(c)
        db.session.commit()
        return c.id_cliente


def test_crear_solicitud(app, client):
    cid = _cliente(app)
    with app.app_context():
        s = SolicitudValidacion(
            id_cliente=cid, tipo='foto', estado='pendiente',
            contexto=json.dumps({'mime': 'image/jpeg'})
        )
        db.session.add(s)
        db.session.commit()
        assert SolicitudValidacion.pendiente_para(cid, 'foto') is not None


def test_pendiente_para_ignora_aprobadas(app, client):
    cid = _cliente(app, num='V601')
    with app.app_context():
        s = SolicitudValidacion(id_cliente=cid, tipo='foto', estado='aprobado', contexto='{}')
        db.session.add(s)
        db.session.commit()
        assert SolicitudValidacion.pendiente_para(cid, 'foto') is None


def test_cancelar_pendiente(app, client):
    cid = _cliente(app, num='V602')
    with app.app_context():
        for _ in range(2):
            db.session.add(SolicitudValidacion(id_cliente=cid, tipo='pago', estado='pendiente', contexto='{}'))
        db.session.commit()
        SolicitudValidacion.cancelar_pendiente(cid, 'pago')
        db.session.commit()
        pendientes = SolicitudValidacion.query.filter_by(
            id_cliente=cid, tipo='pago', estado='pendiente').count()
        canceladas = SolicitudValidacion.query.filter_by(
            id_cliente=cid, tipo='pago', estado='cancelado').count()
        assert pendientes == 0
        assert canceladas == 2


def _login_admin(app, client, email='soladmin@test.com'):
    from models.admin import Admin
    with app.app_context():
        a = Admin(nombre='Admin', email=email,
                  password_hash=generate_password_hash('adminpass'),
                  rol='admin', activo=True)
        db.session.add(a)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': email, 'password': 'adminpass'})


def test_aprobar_foto_aplica_imagen(app, client):
    cid = _cliente(app, num='V603')
    payload = {'mime': 'image/jpeg', 'data': base64.b64encode(b'\xff\xd8\xff\xe0').decode('ascii')}
    with app.app_context():
        s = SolicitudValidacion(id_cliente=cid, tipo='foto', estado='pendiente',
                                contexto=json.dumps(payload))
        db.session.add(s)
        db.session.commit()
        sid = s.id_solicitud
    _login_admin(app, client, email='soladmin1@test.com')
    r = client.post(f'/vitelas/admin/solicitudes/{sid}/aprobar')
    assert r.status_code in (302, 200)
    with app.app_context():
        cli = db.session.get(Cliente, cid)
        assert cli.foto_data == b'\xff\xd8\xff\xe0'


def test_subir_foto_crea_solicitud_pendiente(app, client):
    import io
    from PIL import Image
    cid = _cliente(app, num='V604')
    client.post('/vitelas/login', data={'usuario': 'V604', 'password': 'test123'})
    f1 = io.BytesIO()
    img = Image.new('RGB', (1200, 900), (200, 40, 40))
    img.save(f1, format='PNG')
    f1.seek(0)
    r = client.post('/vitelas/portal/perfil/actualizar',
                    data={'foto': (f1, 'foto.png')},
                    content_type='multipart/form-data', follow_redirects=True)
    assert r.status_code == 200
    assert b'aproba' in r.data.lower()
    with app.app_context():
        s = SolicitudValidacion.pendiente_para(cid, 'foto')
        assert s is not None
        assert s.estado == 'pendiente'


def test_cargar_pago_crea_solicitud_voucher(app, client):
    cid = _cliente(app, num='V605')
    _login_admin(app, client, email='soladmin2@test.com')
    r = client.post('/vitelas/admin/pagos/cargar', data={
        'id_cliente': str(cid),
        'monto': '500',
    })
    assert r.status_code in (302, 200)
    with app.app_context():
        s = SolicitudValidacion.pendiente_para(cid, 'pago')
        assert s is not None
        assert s.estado == 'pendiente'
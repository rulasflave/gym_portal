import pytest
from datetime import date, timedelta
from extensions import db
from models import Cliente, Asistencia, Pago


def test_creating_cliente(app):
    with app.app_context():
        cliente = Cliente(
            numero_registro='001',
            nombre_completo='Juan Perez',
            usuario_login='juan',
            password_hash='hashed_password_123',
            tipo_membresia='Normal',
            fecha_inicio_membresia=date.today(),
            fecha_fin_membresia=date.today() + timedelta(days=30)
        )
        db.session.add(cliente)
        db.session.commit()

        assert cliente.id_cliente is not None
        assert cliente.numero_registro == '001'
        assert cliente.nombre_completo == 'Juan Perez'
        assert cliente.primer_login is True
        assert cliente.activo is True


def test_creating_asistencia(app):
    with app.app_context():
        cliente = Cliente(
            numero_registro='002',
            nombre_completo='Maria Garcia',
            usuario_login='maria',
            password_hash='hashed_password_456'
        )
        db.session.add(cliente)
        db.session.commit()

        asistencia = Asistencia(
            id_cliente=cliente.id_cliente,
            qr_escaneado=True
        )
        db.session.add(asistencia)
        db.session.commit()

        assert asistencia.id_asistencia is not None
        assert asistencia.id_cliente == cliente.id_cliente
        assert asistencia.qr_escaneado is True


def test_membresia_activa_property(app):
    with app.app_context():
        cliente_activo = Cliente(
            numero_registro='003',
            nombre_completo='Activo Test',
            usuario_login='activo',
            password_hash='hash1',
            fecha_inicio_membresia=date.today() - timedelta(days=5),
            fecha_fin_membresia=date.today() + timedelta(days=15)
        )
        cliente_vencido = Cliente(
            numero_registro='004',
            nombre_completo='Vencido Test',
            usuario_login='vencido',
            password_hash='hash2',
            fecha_inicio_membresia=date.today() - timedelta(days=30),
            fecha_fin_membresia=date.today() - timedelta(days=5)
        )
        cliente_futuro = Cliente(
            numero_registro='005',
            nombre_completo='Futuro Test',
            usuario_login='futuro',
            password_hash='hash3',
            fecha_inicio_membresia=date.today() + timedelta(days=10),
            fecha_fin_membresia=date.today() + timedelta(days=30)
        )

        db.session.add_all([cliente_activo, cliente_vencido, cliente_futuro])
        db.session.commit()

        assert cliente_activo.is_membresia_activa is True
        assert cliente_activo.dias_para_vencer == 15

        assert cliente_vencido.is_membresia_activa is False
        assert cliente_futuro.is_membresia_activa is False


def test_membresia_vencida_por_fecha(app):
    with app.app_context():
        cliente = Cliente(
            numero_registro='006',
            nombre_completo='Fecha Vencida',
            usuario_login='fecha',
            password_hash='hash4',
            fecha_inicio_membresia=date.today() - timedelta(days=30),
            fecha_fin_membresia=date.today() - timedelta(days=1)
        )
        db.session.add(cliente)
        db.session.commit()

        assert cliente.is_membresia_activa is False
        assert cliente.dias_para_vencer == 0

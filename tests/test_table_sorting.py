from werkzeug.security import generate_password_hash
from extensions import db
from models.cliente import Cliente
from services.table_sorting import apply_sort


def _mk_cliente(num, nombre, **kw):
    c = Cliente(numero_registro=num, nombre_completo=nombre,
                usuario_login=num, password_hash=generate_password_hash('x'), **kw)
    db.session.add(c)
    db.session.flush()
    return c


def test_apply_sort_valid_key_asc_and_desc(app):
    with app.app_context():
        _mk_cliente('V003', 'Zac')
        _mk_cliente('V001', 'Ana')
        _mk_cliente('V002', 'Bob')
        db.session.commit()
        cols = {'registro': Cliente.numero_registro, 'nombre': Cliente.nombre_completo}
        rows = apply_sort(Cliente.query, 'nombre', 'asc', cols).all()
        assert [r.nombre_completo for r in rows] == ['Ana', 'Bob', 'Zac']
        rows = apply_sort(Cliente.query, 'registro', 'desc', cols).all()
        assert [r.numero_registro for r in rows] == ['V003', 'V002', 'V001']


def test_apply_sort_invalid_key_unchanged(app):
    with app.app_context():
        _mk_cliente('V003', 'Zac')
        _mk_cliente('V001', 'Ana')
        db.session.commit()
        query = Cliente.query.order_by(Cliente.numero_registro)
        rows = apply_sort(query, 'bogus', 'asc', {'nombre': Cliente.nombre_completo}).all()
        assert [r.numero_registro for r in rows] == ['V001', 'V003']


def test_apply_sort_callable_entry(app):
    from datetime import date, timedelta
    with app.app_context():
        _mk_cliente('V010', 'Sin Fecha')
        _mk_cliente('V020', 'Con Fecha', fecha_fin_membresia=date.today() - timedelta(days=1))
        db.session.commit()
        cols = {'estado': lambda d: Cliente.fecha_fin_membresia.asc().nulls_last()
                if d != 'desc' else Cliente.fecha_fin_membresia.desc().nulls_last()}
        rows = apply_sort(Cliente.query, 'estado', 'asc', cols).all()
        assert [r.nombre_completo for r in rows] == ['Con Fecha', 'Sin Fecha']
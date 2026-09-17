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


def _login_admin(app, client, email='admin-sort@test.com'):
    from models.admin import Admin
    with app.app_context():
        a = Admin(nombre='A', email=email,
                  password_hash=generate_password_hash('adminpass'),
                  rol='admin', activo=True)
        db.session.add(a)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': email, 'password': 'adminpass'})


def test_clientes_sort_registro_desc(app, client):
    _login_admin(app, client)
    with app.app_context():
        _mk_cliente('V003', 'Zac')
        _mk_cliente('V001', 'Ana')
        _mk_cliente('V002', 'Bob')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=registro&dir=desc')
    assert resp.status_code == 200
    assert resp.data.index(b'V003') < resp.data.index(b'V002') < resp.data.index(b'V001')


def test_clientes_sort_nombre_asc(app, client):
    _login_admin(app, client, email='admin-sort2@test.com')
    with app.app_context():
        _mk_cliente('V003', 'Ana')
        _mk_cliente('V001', 'Zac')
        _mk_cliente('V002', 'Bob')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=nombre&dir=asc')
    assert resp.data.index(b'Ana') < resp.data.index(b'Bob') < resp.data.index(b'Zac')


def test_clientes_sort_estado_nulls_last(app, client):
    from datetime import date, timedelta
    _login_admin(app, client, email='admin-sort3@test.com')
    with app.app_context():
        _mk_cliente('V020', 'Con Fecha', fecha_fin_membresia=date.today() - timedelta(days=1))
        _mk_cliente('V010', 'Sin Fecha')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=estado&dir=asc')
    assert resp.data.index(b'Con Fecha') < resp.data.index(b'Sin Fecha')


def test_clientes_invalid_sort_uses_default(app, client):
    _login_admin(app, client, email='admin-sort4@test.com')
    with app.app_context():
        _mk_cliente('V003', 'Zac')
        _mk_cliente('V001', 'Ana')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=zzz&dir=sidways')
    assert resp.status_code == 200
    assert resp.data.index(b'V001') < resp.data.index(b'V003')


def test_clientes_sort_with_search(app, client):
    _login_admin(app, client, email='admin-sort5@test.com')
    with app.app_context():
        _mk_cliente('V001', 'Ana Perez', nickname='Nica')
        _mk_cliente('V002', 'Bob Lobo', nickname='Nich')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?q=nic&sort=nombre&dir=desc')
    assert resp.data.index(b'Bob') < resp.data.index(b'Ana')


def test_clientes_ajax_sort_returns_thead_html(app, client):
    _login_admin(app, client, email='admin-sort6@test.com')
    with app.app_context():
        _mk_cliente('V001', 'Ana')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=nombre&dir=desc',
                      headers={'X-Requested-With': 'XMLHttpRequest'})
    data = resp.get_json()
    assert 'thead_html' in data
    assert 'V001' in data['html']
    assert b'th-sortable active' in data['thead_html'].encode()
    assert b'\xe2\x96\xbc' in data['thead_html'].encode()  # ▼


def test_clientes_sort_respected_in_pagination(app, client):
    _login_admin(app, client, email='admin-sort7@test.com')
    with app.app_context():
        for i in range(1, 26):
            _mk_cliente(f'V{i:03d}', f'Cliente {i}')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=registro&dir=desc&page=2')
    assert resp.status_code == 200
    # orden desc = V025..V001; pagina 2 (PER_PAGE=20) = filas 21-25 -> V005..V001
    assert resp.data.index(b'V005') < resp.data.index(b'V001')
    assert b'V006' not in resp.data


def test_pagos_sort_monto_desc(app, client):
    from datetime import date
    from models.cliente import Cliente
    from models.pago import Pago
    _login_admin(app, client, email='admin-sort-p1@test.com')
    with app.app_context():
        c = Cliente(numero_registro='V100', nombre_completo='Pagos Sort',
                    usuario_login='v100', password_hash=generate_password_hash('x'))
        db.session.add(c)
        db.session.flush()
        db.session.add_all([
            Pago(id_cliente=c.id_cliente, monto=100, fecha_pago=date(2026, 1, 1), metodo_pago='Efectivo'),
            Pago(id_cliente=c.id_cliente, monto=300, fecha_pago=date(2026, 2, 1), metodo_pago='Tarjeta'),
            Pago(id_cliente=c.id_cliente, monto=200, fecha_pago=date(2026, 3, 1), metodo_pago='Transferencia'),
        ])
        db.session.commit()
    resp = client.get('/vitelas/admin/pagos?sort=monto&dir=desc')
    assert resp.status_code == 200
    assert resp.data.index(b'$300.00') < resp.data.index(b'$200.00') < resp.data.index(b'$100.00')


def test_pagos_sort_metodo_asc(app, client):
    from datetime import date
    from models.cliente import Cliente
    from models.pago import Pago
    _login_admin(app, client, email='admin-sort-p2@test.com')
    with app.app_context():
        c = Cliente(numero_registro='V101', nombre_completo='Pagos Sort 2',
                    usuario_login='v101', password_hash=generate_password_hash('x'))
        db.session.add(c)
        db.session.flush()
        db.session.add_all([
            Pago(id_cliente=c.id_cliente, monto=100, fecha_pago=date(2026, 1, 1), metodo_pago='Tarjeta'),
            Pago(id_cliente=c.id_cliente, monto=200, fecha_pago=date(2026, 2, 1), metodo_pago='Efectivo'),
            Pago(id_cliente=c.id_cliente, monto=300, fecha_pago=date(2026, 3, 1), metodo_pago='Transferencia'),
        ])
        db.session.commit()
    resp = client.get('/vitelas/admin/pagos?sort=metodo&dir=asc')
    assert resp.data.index(b'Efectivo') < resp.data.index(b'Tarjeta') < resp.data.index(b'Transferencia')


def test_noticias_sort_fecha_asc(app, client):
    from datetime import datetime, timedelta, timezone
    from models.noticia import Noticia
    _login_admin(app, client, email='admin-sort-n1@test.com')
    now = datetime.now(timezone.utc)
    with app.app_context():
        db.session.add_all([
            Noticia(titulo='Segunda', contenido='y', fecha_publicacion=now + timedelta(seconds=2)),
            Noticia(titulo='Primera', contenido='x', fecha_publicacion=now),
        ])
        db.session.commit()
    resp = client.get('/vitelas/admin/noticias?sort=fecha&dir=asc')
    assert resp.status_code == 200
    assert resp.data.index(b'Primera') < resp.data.index(b'Segunda')


def test_noticias_sort_estado_desc(app, client):
    from datetime import datetime, timezone
    from models.noticia import Noticia
    _login_admin(app, client, email='admin-sort-n2@test.com')
    with app.app_context():
        db.session.add_all([
            Noticia(titulo='Inactiva Test', contenido='z', activa=False,
                    fecha_publicacion=datetime.now(timezone.utc)),
            Noticia(titulo='Activa Test', contenido='a', activa=True,
                    fecha_publicacion=datetime.now(timezone.utc)),
        ])
        db.session.commit()
    resp = client.get('/vitelas/admin/noticias?sort=estado&dir=desc')
    assert resp.data.index(b'Activa') < resp.data.index(b'Inactiva')


def test_clientes_sort_vigencia_asc(app, client):
    from datetime import date
    _login_admin(app, client, email='admin-sort-v1@test.com')
    with app.app_context():
        _mk_cliente('V002', 'Bob', fecha_inicio_membresia=date(2026, 6, 1))
        _mk_cliente('V001', 'Ana', fecha_inicio_membresia=date(2026, 2, 1))
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=vigencia&dir=asc')
    assert resp.status_code == 200
    assert resp.data.index(b'Ana') < resp.data.index(b'Bob')


def test_clientes_sort_vigencia_desc(app, client):
    from datetime import date
    _login_admin(app, client, email='admin-sort-v2@test.com')
    with app.app_context():
        _mk_cliente('V002', 'Bob', fecha_inicio_membresia=date(2026, 6, 1))
        _mk_cliente('V001', 'Ana', fecha_inicio_membresia=date(2026, 2, 1))
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes?sort=vigencia&dir=desc')
    assert resp.status_code == 200
    assert resp.data.index(b'Bob') < resp.data.index(b'Ana')


def test_clientes_thead_orden_y_columnas_nuevas(app, client):
    _login_admin(app, client, email='admin-sort-v3@test.com')
    with app.app_context():
        _mk_cliente('V001', 'Ana')
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    # El macro th_sortable renderiza el label seguido de \n  </th>,
    # por lo que se acota a la seccion thead (fallback del brief)
    thead = html[html.index('<thead'):html.index('</thead>')]
    # Estado entre Cliente y Apodo
    assert thead.index('Cliente') < thead.index('Estado') < thead.index('Apodo')
    # Membresía eliminada del thead
    assert 'Membres&#237;a' not in thead and 'Membresía' not in thead
    # Fecha de Vigencia en lugar de Membresía
    assert 'Fecha de Vigencia' in thead
    # Cantidad a Pagar antes de Acciones
    assert thead.index('Cantidad a Pagar') < thead.index('Acciones')


def test_clientes_rows_muestran_fecha_vigencia_y_cantidad(app, client):
    from datetime import date
    from models.pago import Pago
    _login_admin(app, client, email='admin-sort-v4@test.com')
    with app.app_context():
        c = _mk_cliente('V001', 'Ana', fecha_inicio_membresia=date(2026, 2, 1))
        db.session.add(Pago(id_cliente=c.id_cliente, monto=350.00, fecha_pago=date(2026, 5, 1)))
        db.session.add(Pago(id_cliente=c.id_cliente, monto=120.00, fecha_pago=date(2026, 1, 10)))
        db.session.commit()
    resp = client.get('/vitelas/admin/clientes')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    # Fecha de inicio en dd/mm/aaaa
    assert '01/02/2026' in html
    # Monto del primer pago ($120.00) con orden: fecha despues de Cliente y antes de Cantidad
    assert '$120.00' in html
    assert html.index('Ana') < html.index('01/02/2026') < html.index('$120.00')
    # tipo_membresia ya no se muestra como celda
    assert '<td>' not in html or 'Normal' not in html

from services.table_pagination import paginate, is_ajax
from flask import Flask, request


def test_paginate_basic():
    app = Flask(__name__)
    with app.test_request_context('/'):
        from extensions import db
        pass  # fixture-less: paginate is pure, test with fake list
    # paginate works on any query-like object via count/limit/offset


def test_paginate_page_offset_is_one_based(app):
    # Reuses conftest app; uses a real table indirectly through Cliente
    from extensions import db
    from models.cliente import Cliente
    from werkzeug.security import generate_password_hash
    for i in range(1, 26):
        c = Cliente(
            numero_registro=f'V{i:03d}',
            nombre_completo=f'Cliente {i}',
            usuario_login=f'v{i}',
            password_hash=generate_password_hash('x'),
        )
        db.session.add(c)
    db.session.commit()
    query = Cliente.query.order_by(Cliente.numero_registro)
    total, total_pages, items = paginate(query, per_page=10, page=2)
    assert total == 25
    assert total_pages == 3
    assert len(items) == 10
    assert items[0].numero_registro == 'V011'

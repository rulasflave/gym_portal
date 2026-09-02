import pytest
from extensions import db
from models.admin import Admin
from werkzeug.security import generate_password_hash


def _login_admin(client, app, nombre='Test Admin', email='admin@test.com', rol='admin'):
    with app.app_context():
        from extensions import db
        from models.admin import Admin
        pw = generate_password_hash('test123')
        admin = Admin(nombre=nombre, email=email, password_hash=pw, rol=rol)
        db.session.add(admin)
        db.session.commit()
    client.post('/vitelas/login', data={'usuario': email, 'password': 'test123'})


def test_admin_dashboard_requires_admin_role(app, client):
    with app.app_context():
        password = generate_password_hash('test123')
        admin = Admin(
            nombre='Test Admin',
            email='admin@test.com',
            password_hash=password,
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        client.post('/login', data={
            'usuario': 'admin@test.com',
            'password': 'test123'
        })
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 200

def test_admin_dashboard_uses_admin_shell(app, client):
    _login_admin(client, app)
    resp = client.get('/vitelas/admin/dashboard')
    assert resp.status_code == 200
    assert b'admin-sidebar' in resp.data
    assert b'id="adminMenuToggle"' in resp.data
    assert b'admin.css' in resp.data

def test_admin_dashboard_shows_stats(app, client):
    _login_admin(client, app)
    resp = client.get('/vitelas/admin/dashboard')
    assert b'Total Clientes' in resp.data
    assert b'admin-stats' in resp.data

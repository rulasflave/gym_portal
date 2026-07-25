import pytest
from extensions import db
from models.admin import Admin
from werkzeug.security import generate_password_hash

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

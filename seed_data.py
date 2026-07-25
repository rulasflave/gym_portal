from app import create_app
from extensions import db
from models.cliente import Cliente
from models.admin import Admin
from models.noticia import Noticia
from datetime import date
from werkzeug.security import generate_password_hash

def seed_database():
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        if Cliente.query.first():
            print("Database already seeded")
            return
        
        password = generate_password_hash('admin123')
        admin = Admin(
            nombre='Administrador',
            email='admin@gym.com',
            password_hash=password,
            rol='superadmin'
        )
        db.session.add(admin)
        
        clientes_data = [
            {
                'numero_registro': 'V001',
                'nombre_completo': 'Ashley Jatzeny Ulate Sanchez',
                'nickname': 'Bubu',
                'telefono': '3312381421',
                'fecha_nacimiento': date(2014, 9, 12),
                'tipo_membresia': 'Beca',
                'fecha_inicio_membresia': date(2026, 6, 25),
                'fecha_fin_membresia': date(2026, 8, 25)
            },
            {
                'numero_registro': 'V002',
                'nombre_completo': 'Ximena Landeros',
                'nickname': 'Ximena',
                'telefono': '3312616289',
                'fecha_nacimiento': date(2013, 6, 25),
                'tipo_membresia': 'Normal',
                'fecha_inicio_membresia': date(2026, 6, 25),
                'fecha_fin_membresia': date(2026, 8, 25)
            },
            {
                'numero_registro': 'V003',
                'nombre_completo': 'Gael Montes Ulloa',
                'nickname': 'Gael',
                'telefono': '3318745998',
                'email': 'andresmontesulloa@gmail.com',
                'fecha_nacimiento': date(2007, 12, 1),
                'tipo_membresia': 'Programa',
                'fecha_inicio_membresia': date(2026, 6, 25),
                'fecha_fin_membresia': date(2026, 8, 25)
            }
        ]
        
        for data in clientes_data:
            client_password = generate_password_hash('cambiar123')
            cliente = Cliente(
                usuario_login=data['numero_registro'],
                password_hash=client_password,
                primer_login=True,
                **data
            )
            db.session.add(cliente)
        
        noticia = Noticia(
            titulo='¡Bienvenidos al Gym Portal!',
            contenido='Ya puedes consultar tu información en línea. Inicia sesión con tu número de registro.',
            activa=True
        )
        db.session.add(noticia)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
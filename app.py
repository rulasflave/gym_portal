from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models.cliente import Cliente
        from models.admin import Admin
        if user_id.startswith('cliente-'):
            return Cliente.query.get(int(user_id.split('-', 1)[1]))
        if user_id.startswith('admin-'):
            return Admin.query.get(int(user_id.split('-', 1)[1]))
        return None

    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.cliente_portal import cliente_bp
    from routes.admin_portal import admin_bp
    app.register_blueprint(cliente_bp, url_prefix='/portal')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from routes.kiosco import kiosco_bp
    app.register_blueprint(kiosco_bp, url_prefix='/kiosco')

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Initialized the database.")

    @app.cli.command("seed-db")
    def seed_db_command():
        from seed_data import seed_database
        seed_database()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

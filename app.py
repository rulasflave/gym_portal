from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager

def migrate_config_column(app):
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"create_all: {e}")
        try:
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='configuracion_recordatorio' AND column_name='mensaje_whatsapp'"
            ))
            if result.fetchone():
                db.session.execute(db.text(
                    "ALTER TABLE configuracion_recordatorio RENAME COLUMN mensaje_whatsapp TO mensaje_recordatorio"
                ))
                db.session.commit()
                print("Migrated: renamed mensaje_whatsapp to mensaje_recordatorio")
            else:
                print("No migration needed")
        except Exception as e:
            print(f"Migration skip: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
        try:
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='clientes' AND column_name='empresa'"
            ))
            if not result.fetchone():
                db.session.execute(db.text(
                    "ALTER TABLE clientes ADD COLUMN empresa VARCHAR(20)"
                ))
                db.session.commit()
                print("Migrated: added empresa column to clientes")
        except Exception as e:
            print(f"Migration empresa skip: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
        try:
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='clientes' AND column_name='foto_data'"
            ))
            if not result.fetchone():
                db.session.execute(db.text(
                    "ALTER TABLE clientes ADD COLUMN foto_data BYTEA"
                ))
                db.session.execute(db.text(
                    "ALTER TABLE clientes ADD COLUMN foto_mime VARCHAR(50)"
                ))
                db.session.commit()
                print("Migrated: added foto_data and foto_mime columns to clientes")
        except Exception as e:
            print(f"Migration foto skip: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

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

    from routes.configuracion import config_bp
    app.register_blueprint(config_bp)

    migrate_config_column(app)

    try:
        from services.reminder_scheduler import init_scheduler
        init_scheduler(app)
    except Exception as e:
        print(f"Scheduler init error: {e}")

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

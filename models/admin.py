from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id_admin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def get_id(self):
        return f"admin-{self.id_admin}"

    def __repr__(self):
        return f'<Admin {self.nombre} - {self.rol}>'

from datetime import datetime, timezone
from extensions import db


class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    id_mensaje = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    asunto = db.Column(db.String(200), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False, default='')
    imagen_data = db.Column(db.LargeBinary)
    imagen_mime = db.Column(db.String(50))
    es_automatico = db.Column(db.Boolean, default=False)
    leido = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
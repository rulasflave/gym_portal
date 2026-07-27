from datetime import datetime, timezone
from extensions import db


class RecordatorioEnviado(db.Model):
    __tablename__ = 'recordatorios_enviados'

    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    enviado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    exitoso = db.Column(db.Boolean, default=False)

    cliente = db.relationship('Cliente', backref='recordatorios')

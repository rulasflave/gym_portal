from datetime import datetime, timezone
from extensions import db


class Asistencia(db.Model):
    __tablename__ = 'asistencias'

    id_asistencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    fecha_hora_entrada = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    qr_escaneado = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Asistencia {self.id_asistencia} - Cliente {self.id_cliente}>'

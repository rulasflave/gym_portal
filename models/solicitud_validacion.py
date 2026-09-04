from datetime import datetime, timezone
from extensions import db


class SolicitudValidacion(db.Model):
    __tablename__ = 'solicitudes_validacion'

    id_solicitud = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    contexto = db.Column(db.Text, default='{}')
    comentario_admin = db.Column(db.String(500))
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resuelto_en = db.Column(db.DateTime)

    @staticmethod
    def pendiente_para(id_cliente, tipo):
        return SolicitudValidacion.query.filter_by(
            id_cliente=id_cliente, tipo=tipo, estado='pendiente').first()

    @staticmethod
    def cancelar_pendiente(id_cliente, tipo):
        pendientes = SolicitudValidacion.query.filter_by(
            id_cliente=id_cliente, tipo=tipo, estado='pendiente').all()
        for s in pendientes:
            s.estado = 'cancelado'
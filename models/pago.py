from datetime import datetime, timezone
from extensions import db


class Pago(db.Model):
    __tablename__ = 'pagos'

    id_pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    metodo_pago = db.Column(db.String(50))
    concepto = db.Column(db.String(200))
    comprobante_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Pago {self.id_pago} - ${self.monto}>'

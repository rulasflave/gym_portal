from datetime import datetime, date, timezone
from flask_login import UserMixin
from extensions import db


class Cliente(UserMixin, db.Model):
    __tablename__ = 'clientes'

    id_cliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_registro = db.Column(db.String(10), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    nickname = db.Column(db.String(50))
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    foto_url = db.Column(db.String(255))
    foto_data = db.Column(db.LargeBinary)
    foto_mime = db.Column(db.String(50))
    contacto_emergencia = db.Column(db.String(100))
    lesiones_medicas = db.Column(db.Text)
    tipo_membresia = db.Column(db.String(20))
    empresa = db.Column(db.String(20))
    fecha_inicio_membresia = db.Column(db.Date)
    fecha_fin_membresia = db.Column(db.Date)
    usuario_login = db.Column(db.String(10), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    primer_login = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    asistencias = db.relationship('Asistencia', backref='cliente', lazy=True)
    pagos = db.relationship('Pago', backref='cliente', lazy=True)
    mensajes = db.relationship('Mensaje', backref='cliente', lazy=True, cascade='all, delete-orphan')

    @property
    def is_membresia_activa(self):
        if not self.fecha_inicio_membresia or not self.fecha_fin_membresia:
            return False
        hoy = date.today()
        return self.fecha_inicio_membresia <= hoy <= self.fecha_fin_membresia

    @property
    def estado_membresia(self):
        if not self.fecha_inicio_membresia:
            return 'sin_fecha'
        hoy = date.today()
        if self.fecha_inicio_membresia > hoy:
            return 'pendiente'
        if self.fecha_fin_membresia and hoy > self.fecha_fin_membresia:
            return 'vencida'
        if self.fecha_fin_membresia and hoy <= self.fecha_fin_membresia:
            return 'activa'
        return 'sin_fecha'

    @property
    def dias_para_vencer(self):
        if not self.fecha_fin_membresia:
            return None
        delta = self.fecha_fin_membresia - date.today()
        return max(0, delta.days)

    @property
    def dias_vencido(self):
        if self.estado_membresia != 'vencida':
            return None
        delta = date.today() - self.fecha_fin_membresia
        return max(0, delta.days)

    def get_id(self):
        return f"cliente-{self.id_cliente}"

    def __repr__(self):
        return f'<Cliente {self.numero_registro} - {self.nombre_completo}>'

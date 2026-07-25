from datetime import datetime, timezone
from extensions import db


class Noticia(db.Model):
    __tablename__ = 'noticias'

    id_noticia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(255))
    fecha_publicacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    activa = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Noticia {self.id_noticia} - {self.titulo}>'

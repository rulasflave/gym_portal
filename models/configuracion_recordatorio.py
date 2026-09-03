from extensions import db


class ConfiguracionRecordatorio(db.Model):
    __tablename__ = 'configuracion_recordatorio'

    id = db.Column(db.Integer, primary_key=True)
    dias_antes = db.Column(db.Integer, default=3)
    horario_envio = db.Column(db.String(5), default='09:00')
    activo = db.Column(db.Boolean, default=True)
    mensaje_recordatorio = db.Column(db.Text, default=(
        '¡Hola {nombre}! 💪 Tu membresía {tipo} vence en {días} días '
        '({fecha}). ¡Renueva pronto para seguir entrenando!'
    ))
    chat_ids = db.Column(db.Text, nullable=True)

    @classmethod
    def get_config(cls):
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config

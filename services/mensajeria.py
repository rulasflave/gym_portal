from extensions import db
from models.mensaje import Mensaje


def crear_mensaje(id_cliente, asunto, cuerpo, es_automatico=False,
                  imagen_data=None, imagen_mime=None):
    m = Mensaje(
        id_cliente=id_cliente, asunto=asunto, cuerpo=cuerpo,
        es_automatico=es_automatico, leido=False,
        imagen_data=imagen_data, imagen_mime=imagen_mime,
    )
    db.session.add(m)
    return m


def no_leidos(id_cliente):
    return Mensaje.query.filter_by(id_cliente=id_cliente, leido=False).count()
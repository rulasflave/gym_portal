from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

SECCIONES = [
    {'key': 'panel', 'label': 'Panel', 'icon': 'fa-tachometer-alt',
     'endpoint': 'admin.dashboard', 'endpoints': ['admin.dashboard']},
    {'key': 'clientes', 'label': 'Clientes', 'icon': 'fa-user-friends',
     'endpoint': 'admin.clientes',
     'endpoints': ['admin.clientes', 'admin.foto_cliente', 'admin.nuevo_cliente',
                   'admin.editar_cliente', 'admin.eliminar_cliente',
                   'admin.cliente_qr', 'admin.enviar_recordatorio']},
    {'key': 'pagos', 'label': 'Pagos', 'icon': 'fa-dollar-sign',
     'endpoint': 'admin.pagos',
     'endpoints': ['admin.pagos', 'admin.nuevo_pago', 'admin.editar_pago',
                   'admin.eliminar_pago']},
    {'key': 'noticias', 'label': 'Noticias', 'icon': 'fa-newspaper',
     'endpoint': 'admin.noticias',
     'endpoints': ['admin.noticias', 'admin.nueva_noticia', 'admin.editar_noticia']},
    {'key': 'mensajes', 'label': 'Mensajes', 'icon': 'fa-envelope',
     'endpoint': 'admin.mensajes',
     'endpoints': ['admin.mensajes', 'admin.nuevo_mensaje', 'admin.archivo_mensaje']},
    {'key': 'validaciones', 'label': 'Validaciones', 'icon': 'fa-clipboard-check',
     'endpoint': 'admin.solicitudes',
     'endpoints': ['admin.solicitudes', 'admin.solicitud_archivo',
                   'admin.aprobar_solicitud', 'admin.rechazar_solicitud']},
    {'key': 'reportes', 'label': 'Reportes', 'icon': 'fa-chart-bar',
     'endpoint': 'admin.reportes',
     'endpoints': ['admin.reportes', 'admin.reporte_clientes_pdf',
                   'admin.reporte_clientes_excel', 'admin.reporte_pagos_pdf',
                   'admin.reporte_pagos_excel']},
    {'key': 'recordatorios', 'label': 'Recordatorios', 'icon': 'fa-bell',
     'endpoint': 'configuracion.configuracion_recordatorios',
     'endpoints': ['configuracion.configuracion_recordatorios']},
]

SECCION_KEYS = [s['key'] for s in SECCIONES]
ENDPOINT_A_SECCION = {ep: s['key'] for s in SECCIONES for ep in s['endpoints']}


def es_super(admin):
    return getattr(admin, 'rol', None) == 'superadmin'


def _parse_permisos(raw):
    if not raw:
        return []
    return [p.strip().lower() for p in raw.split(',') if p.strip()]


def secciones_de(admin):
    if es_super(admin):
        return list(SECCION_KEYS)
    return _parse_permisos(getattr(admin, 'permisos', None))


def puede(admin, key):
    if es_super(admin):
        return True
    return key in secciones_de(admin)


def seccion_de_endpoint(endpoint):
    return ENDPOINT_A_SECCION.get(endpoint)


def requiere_seccion(key):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not getattr(current_user, 'is_authenticated', False):
                return redirect(url_for('auth.login'))
            if not hasattr(current_user, 'rol'):
                abort(403)
            if not puede(current_user, key):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

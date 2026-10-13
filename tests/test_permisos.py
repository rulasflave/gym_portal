from types import SimpleNamespace
from services.permisos import (
    SECCIONES, SECCION_KEYS, es_super, secciones_de, puede, seccion_de_endpoint,
)


def _admin(rol='admin', permisos=None, activo=True):
    return SimpleNamespace(rol=rol, permisos=permisos, activo=activo)


def test_claves_y_orden():
    assert SECCION_KEYS == ['panel', 'clientes', 'pagos', 'noticias',
                            'mensajes', 'validaciones', 'reportes', 'recordatorios']


def test_es_super():
    assert es_super(_admin(rol='superadmin')) is True
    assert es_super(_admin(rol='admin')) is False


def test_secciones_super_son_todas():
    assert secciones_de(_admin(rol='superadmin')) == SECCION_KEYS


def test_secciones_parsea_csv_y_normaliza():
    a = _admin(permisos=' Clientes, pagos ,NOTICIAS ')
    assert secciones_de(a) == ['clientes', 'pagos', 'noticias']


def test_secciones_null_es_vacio():
    assert secciones_de(_admin(permisos=None)) == []
    assert secciones_de(_admin(permisos='')) == []


def test_puede_super_siempre():
    assert puede(_admin(rol='superadmin', permisos=None), 'pagos') is True


def test_puede_respetando_lista():
    a = _admin(permisos='clientes')
    assert puede(a, 'clientes') is True
    assert puede(a, 'pagos') is False


def test_seccion_de_endpoint_incluye_subacciones():
    assert seccion_de_endpoint('admin.dashboard') == 'panel'
    assert seccion_de_endpoint('admin.nuevo_cliente') == 'clientes'
    assert seccion_de_endpoint('admin.eliminar_pago') == 'pagos'
    assert seccion_de_endpoint('admin.aprobar_solicitud') == 'validaciones'
    assert seccion_de_endpoint('admin.reporte_pagos_pdf') == 'reportes'
    assert seccion_de_endpoint('configuracion.configuracion_recordatorios') == 'recordatorios'
    assert seccion_de_endpoint('admin.administradores') is None
    assert seccion_de_endpoint('algo.desconocido') is None

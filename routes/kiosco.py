from flask import Blueprint, render_template, request, jsonify
from models.cliente import Cliente
from models.asistencia import Asistencia
from extensions import db
from datetime import datetime, date

kiosco_bp = Blueprint('kiosco', __name__)

@kiosco_bp.route('/')
def scanner():
    return render_template('kiosco/scanner.html')

@kiosco_bp.route('/validar', methods=['POST'])
def validar_codigo():
    codigo = request.json.get('codigo')
    
    cliente = Cliente.query.filter_by(numero_registro=codigo).first()
    
    if not cliente:
        return jsonify({
            'status': 'error',
            'message': 'Código no válido. Consulta en recepción.'
        })
    
    if not cliente.is_membresia_activa:
        return jsonify({
            'status': 'vencida',
            'message': f'Tu membresía venció el {cliente.fecha_fin_membresia.strftime("%d/%m/%Y")}. Renueva para continuar.',
            'nombre': cliente.nickname or cliente.nombre_completo
        })
    
    asistencia = Asistencia(
        id_cliente=cliente.id_cliente,
        fecha_hora_entrada=datetime.now(),
        qr_escaneado=True
    )
    db.session.add(asistencia)
    db.session.commit()
    
    hoy = datetime.now().date()
    es_cumple = False
    if cliente.fecha_nacimiento:
        es_cumple = cliente.fecha_nacimiento.month == hoy.month and cliente.fecha_nacimiento.day == hoy.day
    
    # Check if membership expires in 3 days or less
    dias_restantes = None
    alerta_vencimiento = False
    if cliente.fecha_fin_membresia:
        delta = cliente.fecha_fin_membresia - hoy
        dias_restantes = delta.days
        if dias_restantes <= 3:
            alerta_vencimiento = True
    
    return jsonify({
        'status': 'ok',
        'nombre': cliente.nickname or cliente.nombre_completo,
        'nombre_completo': cliente.nombre_completo,
        'numero_registro': cliente.numero_registro,
        'foto_url': f'/static/uploads/{cliente.foto_url}' if cliente.foto_url else None,
        'tipo_membresia': cliente.tipo_membresia,
        'fecha_fin': cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else None,
        'es_cumpleanos': es_cumple,
        'alerta_vencimiento': alerta_vencimiento,
        'dias_restantes': dias_restantes,
        'mensaje': f'¡Feliz cumpleaños {cliente.nickname or cliente.nombre_completo}! 🎂🎉' if es_cumple else f'Bienvenido {cliente.nickname or cliente.nombre_completo}!'
    })

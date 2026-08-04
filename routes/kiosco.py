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
    codigo = request.json.get('codigo', '').strip().upper()
    
    cliente = Cliente.query.filter_by(numero_registro=codigo).first()
    
    if not cliente:
        return jsonify({
            'status': 'error',
            'message': 'Código no válido. Consulta en recepción.'
        })
    
    hoy = datetime.now().date()
    
    if not cliente.is_membresia_activa:
        # Check if within 2-day grace period
        if cliente.fecha_fin_membresia:
            dias_expirado = (hoy - cliente.fecha_fin_membresia).days
            if dias_expirado <= 2:
                # Allow access with warning
                asistencia = Asistencia(
                    id_cliente=cliente.id_cliente,
                    fecha_hora_entrada=datetime.now(),
                    qr_escaneado=True
                )
                db.session.add(asistencia)
                db.session.commit()
                
                return jsonify({
                    'status': 'ok',
                    'grace_period': True,
                    'dias_expirado': dias_expirado,
                    'nombre': cliente.nickname or cliente.nombre_completo,
                    'nombre_completo': cliente.nombre_completo,
                    'numero_registro': cliente.numero_registro,
                    'foto_url': f'/admin/foto/{cliente.id_cliente}' if cliente.foto_data else None,
                    'tipo_membresia': cliente.tipo_membresia,
                    'fecha_fin': cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else None,
                    'es_cumpleanos': False,
                    'alerta_vencimiento': False,
                    'dias_restantes': None,
                    'mensaje': f'⚠️ Días de gracia: {dias_expirado}/2. ¡Renueva ya!'
                })
        
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
    
    es_cumple = False
    if cliente.fecha_nacimiento:
        es_cumple = cliente.fecha_nacimiento.month == hoy.month and cliente.fecha_nacimiento.day == hoy.day
    
    dias_restantes = None
    alerta_vencimiento = False
    if cliente.fecha_fin_membresia:
        delta = cliente.fecha_fin_membresia - hoy
        dias_restantes = delta.days
        if dias_restantes <= 3:
            alerta_vencimiento = True
    
    return jsonify({
        'status': 'ok',
        'grace_period': False,
        'nombre': cliente.nickname or cliente.nombre_completo,
        'nombre_completo': cliente.nombre_completo,
        'numero_registro': cliente.numero_registro,
        'foto_url': f'/admin/foto/{cliente.id_cliente}' if cliente.foto_data else None,
        'tipo_membresia': cliente.tipo_membresia,
        'fecha_fin': cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else None,
        'es_cumpleanos': es_cumple,
        'alerta_vencimiento': alerta_vencimiento,
        'dias_restantes': dias_restantes,
        'mensaje': f'¡Feliz cumpleaños {cliente.nickname or cliente.nombre_completo}! 🎂🎉' if es_cumple else f'Bienvenido {cliente.nickname or cliente.nombre_completo}!'
    })

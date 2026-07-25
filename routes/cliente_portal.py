from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models.asistencia import Asistencia
from models.pago import Pago
from models.noticia import Noticia
from werkzeug.security import generate_password_hash
from services.qr_service import generate_qr_code
from extensions import db

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/dashboard')
@login_required
def dashboard():
    asistencias = Asistencia.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Asistencia.fecha_hora_entrada.desc()).limit(10).all()
    noticias = Noticia.query.filter_by(activa=True)\
        .order_by(Noticia.fecha_publicacion.desc()).limit(5).all()
    return render_template('cliente/dashboard.html', 
                         asistencias=asistencias, noticias=noticias)

@cliente_bp.route('/perfil')
@login_required
def perfil():
    return render_template('cliente/perfil.html')

@cliente_bp.route('/mi-qr')
@login_required
def mi_qr():
    qr_data = generate_qr_code(current_user.numero_registro)
    return render_template('cliente/mi_qr.html', qr_data=qr_data)

@cliente_bp.route('/asistencias')
@login_required
def asistencias():
    page = request.args.get('page', 1, type=int)
    asistencias = Asistencia.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Asistencia.fecha_hora_entrada.desc())\
        .paginate(page=page, per_page=20)
    return render_template('cliente/asistencias.html', asistencias=asistencias)

@cliente_bp.route('/pagos')
@login_required
def pagos():
    pagos = Pago.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Pago.fecha_pago.desc()).all()
    return render_template('cliente/pagos.html', pagos=pagos)

@cliente_bp.route('/noticias')
@login_required
def noticias():
    noticias = Noticia.query.filter_by(activa=True)\
        .order_by(Noticia.fecha_publicacion.desc()).all()
    return render_template('cliente/noticias.html', noticias=noticias)

@cliente_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')
        confirmar = request.form.get('confirmar_password')
        
        if nueva_password != confirmar:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('cliente.cambiar_password'))
        
        current_user.password_hash = generate_password_hash(nueva_password)
        current_user.primer_login = False
        db.session.commit()
        
        flash('Contraseña actualizada', 'success')
        return redirect(url_for('cliente.dashboard'))
    
    return render_template('cliente/cambiar_password.html')

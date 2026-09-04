from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_required, current_user
from models.asistencia import Asistencia
from models.pago import Pago
from models.noticia import Noticia
from werkzeug.security import generate_password_hash
from services.qr_service import generate_qr_code
from routes.admin_portal import save_photo
from extensions import db

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/dashboard')
@login_required
def dashboard():
    hoy = date.today()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    inicio_siguiente = datetime(hoy.year + (1 if hoy.month == 12 else 0),
                                (1 if hoy.month == 12 else hoy.month + 1), 1)
    asistencias_del_mes = Asistencia.query.filter(
        Asistencia.id_cliente == current_user.id_cliente,
        Asistencia.fecha_hora_entrada >= inicio_mes,
        Asistencia.fecha_hora_entrada < inicio_siguiente
    ).count()

    objetivo_mensual = 24  # 24 asistencias = 100% del objetivo mensual
    pct_donut = round(min(100, asistencias_del_mes / objetivo_mensual * 100))

    visitas = Asistencia.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Asistencia.fecha_hora_entrada.desc()).limit(5).all()

    noticias = Noticia.query.filter_by(activa=True)\
        .order_by(Noticia.fecha_publicacion.desc()).limit(3).all()

    qr_data = generate_qr_code(current_user.numero_registro)
    al_dia = current_user.is_membresia_activa

    return render_template('cliente/dashboard.html',
        asistencias_del_mes=asistencias_del_mes,
        objetivo_mensual=objetivo_mensual,
        pct_donut=pct_donut,
        visitas=visitas,
        noticias=noticias,
        qr_data=qr_data,
        al_dia=al_dia)

@cliente_bp.route('/perfil')
@login_required
def perfil():
    return redirect(url_for('cliente.dashboard'))

@cliente_bp.route('/perfil/actualizar', methods=['POST'])
@login_required
def perfil_actualizar():
    current_user.nickname = request.form.get('nickname', '').strip() or None
    current_user.telefono = request.form.get('telefono', '').strip() or None
    current_user.email = request.form.get('email', '').strip() or None
    current_user.contacto_emergencia = request.form.get('contacto_emergencia', '').strip() or None
    current_user.lesiones_medicas = request.form.get('lesiones_medicas', '').strip() or None

    if 'foto' in request.files and request.files['foto'].filename:
        foto_url, foto_data, foto_mime = save_photo(request.files['foto'])
        if foto_data:
            current_user.foto_data = foto_data
            current_user.foto_mime = foto_mime
            current_user.foto_url = None

    db.session.commit()
    flash('Tus datos fueron actualizados', 'success')
    return redirect(url_for('cliente.dashboard'))

@cliente_bp.route('/mi-qr')
@login_required
def mi_qr():
    qr_data = generate_qr_code(current_user.numero_registro)
    return render_template('cliente/mi_qr.html', qr_data=qr_data)

@cliente_bp.route('/asistencias')
@login_required
def asistencias():
    page = max(1, request.args.get('page', 1, type=int) or 1)
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
        nueva_password = request.form.get('nueva_password', '')
        confirmar = request.form.get('confirmar_password', '')

        if not nueva_password or len(nueva_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('cliente.cambiar_password'))

        if nueva_password != confirmar:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('cliente.cambiar_password'))

        current_user.password_hash = generate_password_hash(nueva_password)
        current_user.primer_login = False
        db.session.commit()

        flash('Contraseña actualizada', 'success')
        return redirect(url_for('cliente.dashboard'))

    return render_template('cliente/cambiar_password.html')


@cliente_bp.route('/bandeja')
@login_required
def bandeja():
    from models.mensaje import Mensaje
    mensajes = Mensaje.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Mensaje.creado_en.desc()).all()
    abrir_id = request.args.get('abrir', type=int)
    mensaje_abierto = None
    if abrir_id:
        mensaje_abierto = Mensaje.query.filter_by(
            id_cliente=current_user.id_cliente, id_mensaje=abrir_id).first()
    if mensaje_abierto is None and mensajes:
        mensaje_abierto = mensajes[0]
    if mensaje_abierto is not None and not mensaje_abierto.leido:
        mensaje_abierto.leido = True
        db.session.commit()
    return render_template('cliente/bandeja.html',
                           mensajes=mensajes, mensaje_abierto=mensaje_abierto)


@cliente_bp.route('/bandeja/<int:id_mensaje>/leer', methods=['POST'])
@login_required
def marcar_leido(id_mensaje):
    from models.mensaje import Mensaje
    from services.mensajeria import no_leidos
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first()
    if m and not m.leido:
        m.leido = True
        db.session.commit()
    return {'no_leidos': no_leidos(current_user.id_cliente)}


@cliente_bp.route('/bandeja/<int:id_mensaje>/imagen')
@login_required
def mensaje_imagen(id_mensaje):
    from models.mensaje import Mensaje
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first_or_404()
    if not m.imagen_data:
        return ('', 404)
    return Response(m.imagen_data, mimetype=m.imagen_mime or 'image/jpeg')

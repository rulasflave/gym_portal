from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, Response, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models.asistencia import Asistencia
from models.pago import Pago
from models.noticia import Noticia
from models.solicitud_validacion import SolicitudValidacion
from services.qr_service import generate_qr_code
from services.branding import is_axis
from routes.admin_portal import save_photo
from extensions import db
import base64
import json

axis_bp = Blueprint('axis', __name__)


def axis_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, '__class__', None).__name__ != 'Cliente' \
                or not is_axis(current_user.empresa):
            abort(404)
        return view(*args, **kwargs)
    return wrapped


@axis_bp.route('/dashboard')
@axis_required
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

    objetivo_mensual = 24
    pct_donut = round(min(100, asistencias_del_mes / objetivo_mensual * 100))

    visitas = Asistencia.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Asistencia.fecha_hora_entrada.desc()).limit(5).all()

    noticias = Noticia.query.filter_by(activa=True)\
        .order_by(Noticia.fecha_publicacion.desc()).limit(3).all()

    qr_data = generate_qr_code(current_user.numero_registro)
    al_dia = current_user.is_membresia_activa

    return render_template('axis/dashboard.html',
        asistencias_del_mes=asistencias_del_mes,
        objetivo_mensual=objetivo_mensual,
        pct_donut=pct_donut,
        visitas=visitas,
        noticias=noticias,
        qr_data=qr_data,
        al_dia=al_dia)


@axis_bp.route('/perfil')
@axis_required
def perfil():
    return redirect(url_for('axis.dashboard'))


@axis_bp.route('/perfil/actualizar', methods=['POST'])
@axis_required
def perfil_actualizar():
    current_user.nickname = request.form.get('nickname', '').strip() or None
    current_user.telefono = request.form.get('telefono', '').strip() or None
    current_user.email = request.form.get('email', '').strip() or None
    current_user.contacto_emergencia = request.form.get('contacto_emergencia', '').strip() or None
    current_user.lesiones_medicas = request.form.get('lesiones_medicas', '').strip() or None

    if 'foto' in request.files and request.files['foto'].filename:
        _, foto_data, foto_mime = save_photo(request.files['foto'])
        if foto_data:
            SolicitudValidacion.cancelar_pendiente(current_user.id_cliente, 'foto')
            contexto = json.dumps({'mime': foto_mime, 'data': base64.b64encode(foto_data).decode('ascii')})
            db.session.add(SolicitudValidacion(
                id_cliente=current_user.id_cliente, tipo='foto',
                estado='pendiente', contexto=contexto))
            flash('Foto enviada, a la espera de aprobación', 'success')

    db.session.commit()
    flash('Tus datos fueron actualizados', 'success')
    return redirect(url_for('axis.dashboard'))


ENTRENAMIENTO_CAMPOS = [
    'wod_grace', 'wod_filthy50', 'wod_fight_gone_bad', 'wod_murph',
    'wod_max_pull_ups', 'wod_fran', 'wod_sprint_400m', 'wod_helen', 'wod_run_5km',
    'lift_clean_jerk', 'lift_snatch', 'lift_deadlift', 'lift_back_squat',
    'lift_bench_press', 'lift_overhead_squat',
    'atleta_box', 'atleta_peso', 'atleta_estatura', 'atleta_talla_playera',
    'atleta_tipo_sangre',
]


@axis_bp.route('/entrenamiento', methods=['GET', 'POST'])
@axis_required
def entrenamiento():
    if request.method == 'POST':
        for campo in ENTRENAMIENTO_CAMPOS:
            setattr(current_user, campo, request.form.get(campo, '').strip() or None)
        db.session.commit()
        flash('Entrenamiento actualizado', 'success')
        return redirect(url_for('axis.entrenamiento'))
    return render_template('axis/entrenamiento.html')


@axis_bp.route('/mi-qr')
@axis_required
def mi_qr():
    qr_data = generate_qr_code(current_user.numero_registro)
    return render_template('axis/mi_qr.html', qr_data=qr_data)


@axis_bp.route('/asistencias')
@axis_required
def asistencias():
    page = max(1, request.args.get('page', 1, type=int) or 1)
    asistencias = Asistencia.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Asistencia.fecha_hora_entrada.desc())\
        .paginate(page=page, per_page=20)
    return render_template('axis/asistencias.html', asistencias=asistencias)


@axis_bp.route('/pagos')
@axis_required
def pagos():
    pagos = Pago.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Pago.fecha_pago.desc()).all()
    return render_template('axis/pagos.html', pagos=pagos)


@axis_bp.route('/pagos/cargar', methods=['GET', 'POST'])
@axis_required
def pagos_cargar():
    if request.method == 'POST':
        monto = request.form.get('monto', '').strip()
        _, vo_data, vo_mime = save_photo(request.files.get('voucher'))
        ctx = {'mime': vo_mime, 'data': base64.b64encode(vo_data).decode('ascii')} if vo_data else {}
        if monto:
            ctx['monto'] = monto
        if not vo_data:
            flash('Adjunta una foto del comprobante de pago', 'error')
            return render_template('axis/pagos_cargar.html')
        SolicitudValidacion.cancelar_pendiente(current_user.id_cliente, 'pago')
        db.session.add(SolicitudValidacion(
            id_cliente=current_user.id_cliente, tipo='pago',
            estado='pendiente', contexto=json.dumps(ctx)))
        db.session.commit()
        flash('Pago enviado. A la espera de aprobación', 'success')
        return redirect(url_for('axis.pagos'))
    return render_template('axis/pagos_cargar.html')


@axis_bp.route('/noticias')
@axis_required
def noticias():
    noticias = Noticia.query.filter_by(activa=True)\
        .order_by(Noticia.fecha_publicacion.desc()).all()
    return render_template('axis/noticias.html', noticias=noticias)


@axis_bp.route('/cambiar-password', methods=['GET', 'POST'])
@axis_required
def cambiar_password():
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password', '')
        confirmar = request.form.get('confirmar_password', '')

        if not nueva_password or len(nueva_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('axis.cambiar_password'))

        if nueva_password != confirmar:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('axis.cambiar_password'))

        current_user.password_hash = generate_password_hash(nueva_password)
        current_user.primer_login = False
        db.session.commit()

        flash('Contraseña actualizada', 'success')
        return redirect(url_for('axis.dashboard'))

    return render_template('axis/cambiar_password.html')


@axis_bp.route('/bandeja')
@axis_required
def bandeja():
    from models.mensaje import Mensaje
    mensajes = Mensaje.query.filter_by(id_cliente=current_user.id_cliente)\
        .order_by(Mensaje.creado_en.desc()).all()
    return render_template('axis/bandeja.html', mensajes=mensajes)


@axis_bp.route('/bandeja/<int:id_mensaje>/leer', methods=['POST'])
@axis_required
def marcar_leido(id_mensaje):
    from models.mensaje import Mensaje
    from services.mensajeria import no_leidos
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first()
    if m and not m.leido:
        m.leido = True
        db.session.commit()
    return {'no_leidos': no_leidos(current_user.id_cliente)}


@axis_bp.route('/mensajes/<int:id_mensaje>')
@axis_required
def detalle_mensaje(id_mensaje):
    from models.mensaje import Mensaje
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first_or_404()
    if not m.leido:
        m.leido = True
        db.session.commit()
    return render_template('axis/mensaje_detalle.html', mensaje=m)


@axis_bp.route('/mensajes/<int:id_mensaje>/eliminar', methods=['POST'])
@axis_required
def eliminar_mensaje(id_mensaje):
    from models.mensaje import Mensaje
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first_or_404()
    db.session.delete(m)
    db.session.commit()
    flash('Mensaje eliminado', 'success')
    return redirect(url_for('axis.bandeja'))


@axis_bp.route('/bandeja/<int:id_mensaje>/imagen')
@axis_required
def mensaje_imagen(id_mensaje):
    from models.mensaje import Mensaje
    m = Mensaje.query.filter_by(id_cliente=current_user.id_cliente,
                                id_mensaje=id_mensaje).first_or_404()
    if not m.imagen_data:
        return ('', 404)
    return Response(m.imagen_data, mimetype=m.imagen_mime or 'image/jpeg')

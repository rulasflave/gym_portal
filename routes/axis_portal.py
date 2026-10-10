from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
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


def _en_progreso(*args, **kwargs):
    return redirect(url_for('axis.dashboard'))


@axis_bp.route('/entrenamiento', methods=['GET', 'POST'])
@axis_required
def entrenamiento():
    return redirect(url_for('axis.dashboard'))


@axis_bp.route('/mi-qr')
@axis_required
def mi_qr():
    return _en_progreso()


@axis_bp.route('/asistencias')
@axis_required
def asistencias():
    return _en_progreso()


@axis_bp.route('/pagos')
@axis_required
def pagos():
    return _en_progreso()


@axis_bp.route('/pagos/cargar', methods=['GET', 'POST'])
@axis_required
def pagos_cargar():
    return _en_progreso()


@axis_bp.route('/noticias')
@axis_required
def noticias():
    return _en_progreso()


@axis_bp.route('/cambiar-password', methods=['GET', 'POST'])
@axis_required
def cambiar_password():
    return _en_progreso()


@axis_bp.route('/bandeja')
@axis_required
def bandeja():
    return _en_progreso()


@axis_bp.route('/bandeja/<int:id_mensaje>/leer', methods=['POST'])
@axis_required
def marcar_leido(id_mensaje):
    return _en_progreso()


@axis_bp.route('/mensajes/<int:id_mensaje>')
@axis_required
def detalle_mensaje(id_mensaje):
    return _en_progreso()


@axis_bp.route('/mensajes/<int:id_mensaje>/eliminar', methods=['POST'])
@axis_required
def eliminar_mensaje(id_mensaje):
    return _en_progreso()


@axis_bp.route('/bandeja/<int:id_mensaje>/imagen')
@axis_required
def mensaje_imagen(id_mensaje):
    return _en_progreso()

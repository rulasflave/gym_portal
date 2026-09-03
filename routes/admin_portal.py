from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, Response, jsonify
from flask_login import login_required, current_user
from models.cliente import Cliente
from models.asistencia import Asistencia
from models.pago import Pago
from models.noticia import Noticia
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from models.recordatorio_enviado import RecordatorioEnviado
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from services.qr_service import generate_qr_code
from services.notification_service import send_telegram
from extensions import db
from datetime import datetime, timedelta
import io
import os

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'rol'):
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_clientes = Cliente.query.filter_by(activo=True).count()
    membresias_activas = Cliente.query.filter(Cliente.fecha_fin_membresia >= datetime.now().date(), Cliente.fecha_inicio_membresia <= datetime.now().date()).count()
    membresias_vencidas = Cliente.query.filter(Cliente.fecha_fin_membresia < datetime.now().date()).count()
    return render_template('admin/dashboard.html',
                         total_clientes=total_clientes,
                         membresias_activas=membresias_activas,
                         membresias_vencidas=membresias_vencidas)

@admin_bp.route('/clientes')
@login_required
@admin_required
def clientes():
    from services.table_pagination import paginate, is_ajax
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Cliente.query.order_by(Cliente.numero_registro)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Cliente.numero_registro.ilike(like),
            Cliente.nombre_completo.ilike(like),
            Cliente.nickname.ilike(like),
            Cliente.telefono.ilike(like),
        ))
    total, total_pages, clientes = paginate(query, page=page)

    if is_ajax():
        rows_html = render_template('admin/_table_rows.html', clientes=clientes)
        return jsonify(html=rows_html, total=total, total_pages=total_pages, page=page)

    return render_template('admin/clientes.html',
                           clientes=clientes, total=total,
                           total_pages=total_pages, page=page, q=q)

def save_photo(file):
    if file and file.filename and allowed_file(file.filename):
        try:
            im = Image.open(file)
            im.thumbnail((300, 300))
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGB')
            buf = io.BytesIO()
            im.save(buf, format='JPEG', quality=80, optimize=True)
            buf.seek(0)
            return None, buf.read(), 'image/jpeg'
        except Exception:
            return None, None, None
    return None, None, None

@admin_bp.route('/foto/<int:id_cliente>')
def foto_cliente(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    if cliente.foto_data:
        return Response(cliente.foto_data, mimetype=cliente.foto_mime or 'image/jpeg')
    return redirect(url_for('static', filename='uploads/' + cliente.foto_url)) if cliente.foto_url else ('', 404)

@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_cliente():
    if request.method == 'POST':
        numero_registro = request.form.get('numero_registro', '').strip().upper()
        
        if Cliente.query.filter_by(numero_registro=numero_registro).first():
            flash('El número de registro ya existe', 'error')
            return redirect(url_for('admin.nuevo_cliente'))
        
        password = generate_password_hash('cambiar123')
        
        foto_url = None
        foto_data = None
        foto_mime = None
        if 'foto' in request.files:
            foto_url, foto_data, foto_mime = save_photo(request.files['foto'])
        
        fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date() if request.form.get('fecha_inicio') else None
        fecha_fin_input = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date() if request.form.get('fecha_fin') else None
        if fecha_inicio and not fecha_fin_input:
            fecha_fin = fecha_inicio + timedelta(days=30)
        else:
            fecha_fin = fecha_fin_input
        
        cliente = Cliente(
            numero_registro=numero_registro,
            nombre_completo=request.form.get('nombre_completo'),
            nickname=request.form.get('nickname'),
            telefono=request.form.get('telefono'),
            email=request.form.get('email'),
            fecha_nacimiento=datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date() if request.form.get('fecha_nacimiento') else None,
            contacto_emergencia=request.form.get('contacto_emergencia'),
            lesiones_medicas=request.form.get('lesiones_medicas'),
            tipo_membresia=request.form.get('tipo_membresia'),
            empresa=request.form.get('empresa'),
            fecha_inicio_membresia=fecha_inicio,
            fecha_fin_membresia=fecha_fin,
            usuario_login=numero_registro,
            password_hash=password,
            primer_login=True,
            foto_url=foto_url,
            foto_data=foto_data,
            foto_mime=foto_mime
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        flash('Cliente creado exitosamente', 'success')
        return redirect(url_for('admin.clientes'))
    
    all_clientes = Cliente.query.all()
    max_num = 0
    for c in all_clientes:
        if c.numero_registro and c.numero_registro.upper().startswith('V'):
            try:
                num = int(c.numero_registro[1:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    next_num = max_num + 1
    next_registro = f"V{next_num:03d}"
    
    return render_template('admin/cliente_form.html', next_registro=next_registro)

@admin_bp.route('/clientes/<int:id_cliente>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_cliente(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    try:
        RecordatorioEnviado.query.filter_by(id_cliente=cliente.id_cliente).delete()
        Asistencia.query.filter_by(id_cliente=cliente.id_cliente).delete()
        Pago.query.filter_by(id_cliente=cliente.id_cliente).delete()
        db.session.flush()
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Cliente {cliente.nombre_completo} eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    return redirect(url_for('admin.clientes'))

@admin_bp.route('/clientes/<int:id_cliente>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cliente(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    
    if request.method == 'POST':
        cliente.nombre_completo = request.form.get('nombre_completo')
        cliente.nickname = request.form.get('nickname')
        cliente.telefono = request.form.get('telefono')
        cliente.email = request.form.get('email')
        cliente.fecha_nacimiento = datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date() if request.form.get('fecha_nacimiento') else None
        cliente.contacto_emergencia = request.form.get('contacto_emergencia')
        cliente.lesiones_medicas = request.form.get('lesiones_medicas')
        cliente.tipo_membresia = request.form.get('tipo_membresia')
        cliente.empresa = request.form.get('empresa')
        cliente.fecha_inicio_membresia = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date() if request.form.get('fecha_inicio') else None
        cliente.fecha_fin_membresia = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date() if request.form.get('fecha_fin') else None
        if cliente.fecha_inicio_membresia and not cliente.fecha_fin_membresia:
            cliente.fecha_fin_membresia = cliente.fecha_inicio_membresia + timedelta(days=30)
        
        if 'foto' in request.files and request.files['foto'].filename:
            _, foto_data, foto_mime = save_photo(request.files['foto'])
            if foto_data:
                cliente.foto_data = foto_data
                cliente.foto_mime = foto_mime
                cliente.foto_url = None
        
        db.session.commit()
        
        flash('Cliente actualizado', 'success')
        return redirect(url_for('admin.clientes'))
    
    return render_template('admin/cliente_form.html', cliente=cliente)

@admin_bp.route('/pagos')
@login_required
@admin_required
def pagos():
    from services.table_pagination import paginate, is_ajax
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Pago.query.join(Cliente, Pago.id_cliente == Cliente.id_cliente).order_by(Pago.fecha_pago.desc())
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Cliente.numero_registro.ilike(like),
            Cliente.nombre_completo.ilike(like),
            Pago.concepto.ilike(like),
            Pago.metodo_pago.ilike(like),
        ))
    total, total_pages, pagos = paginate(query, page=page)
    if is_ajax():
        return jsonify(html=render_template('admin/_pago_rows.html', pagos=pagos),
                       total=total, total_pages=total_pages, page=page)
    return render_template('admin/pagos.html', pagos=pagos, total=total,
                           total_pages=total_pages, page=page, q=q)

@admin_bp.route('/pagos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_pago():
    if request.method == 'POST':
        id_cliente = request.form.get('id_cliente')
        cliente = Cliente.query.get_or_404(int(id_cliente))
        fecha_pago = datetime.strptime(request.form.get('fecha_pago'), '%Y-%m-%d').date()
        
        pago = Pago(
            id_cliente=int(id_cliente),
            monto=float(request.form.get('monto', 0)),
            fecha_pago=fecha_pago,
            metodo_pago=request.form.get('metodo_pago'),
            concepto=request.form.get('concepto')
        )
        
        db.session.add(pago)
        
        # Auto-update membership dates
        cliente.fecha_inicio_membresia = fecha_pago
        cliente.fecha_fin_membresia = fecha_pago + timedelta(days=30)
        
        db.session.commit()
        
        flash(f'Pago registrado. Membresía de {cliente.nombre_completo} actualizada hasta el {cliente.fecha_fin_membresia.strftime("%d/%m/%Y")}', 'success')
        return redirect(url_for('admin.pagos'))
    
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    return render_template('admin/pago_form.html', clientes=clientes, today=datetime.now().strftime('%Y-%m-%d'), pago=None)

@admin_bp.route('/pagos/<int:id_pago>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_pago(id_pago):
    pago = Pago.query.get_or_404(id_pago)
    if request.method == 'POST':
        pago.id_cliente = int(request.form.get('id_cliente'))
        pago.monto = float(request.form.get('monto', 0))
        pago.fecha_pago = datetime.strptime(request.form.get('fecha_pago'), '%Y-%m-%d').date()
        pago.metodo_pago = request.form.get('metodo_pago')
        pago.concepto = request.form.get('concepto')
        db.session.commit()
        flash('Pago actualizado', 'success')
        return redirect(url_for('admin.pagos'))
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    return render_template('admin/pago_form.html', clientes=clientes, pago=pago)

@admin_bp.route('/pagos/<int:id_pago>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_pago(id_pago):
    pago = Pago.query.get_or_404(id_pago)
    db.session.delete(pago)
    db.session.commit()
    flash('Pago eliminado', 'success')
    return redirect(url_for('admin.pagos'))

@admin_bp.route('/noticias')
@login_required
@admin_required
def noticias():
    from services.table_pagination import paginate, is_ajax
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Noticia.query.order_by(Noticia.fecha_publicacion.desc())
    if q:
        query = query.filter(Noticia.titulo.ilike(f'%{q}%'))
    total, total_pages, noticias = paginate(query, page=page)
    if is_ajax():
        return jsonify(html=render_template('admin/_noticia_rows.html', noticias=noticias),
                       total=total, total_pages=total_pages, page=page)
    return render_template('admin/noticias.html', noticias=noticias, total=total,
                           total_pages=total_pages, page=page, q=q)

@admin_bp.route('/noticias/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def nueva_noticia():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')
        imagen_url = request.form.get('imagen_url')
        activa = request.form.get('activa') == 'on'
        
        imagen_file = request.files.get('imagen_file')
        if imagen_file and imagen_file.filename:
            import os
            from flask import current_app
            ext = imagen_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ('jpg', 'jpeg', 'png', 'gif'):
                filename = f"noticia_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'noticias')
                os.makedirs(upload_dir, exist_ok=True)
                imagen_file.save(os.path.join(upload_dir, filename))
                imagen_url = f"/static/uploads/noticias/{filename}"
        
        noticia = Noticia(
            titulo=titulo,
            contenido=contenido,
            imagen_url=imagen_url if imagen_url else None,
            activa=activa
        )
        db.session.add(noticia)
        db.session.commit()
        flash('Noticia creada exitosamente', 'success')
        return redirect(url_for('admin.noticias'))
    
    return render_template('admin/noticia_form.html', noticia=None, titulo='Nueva Noticia')

@admin_bp.route('/noticias/editar/<int:id_noticia>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_noticia(id_noticia):
    noticia = Noticia.query.get_or_404(id_noticia)
    
    if request.method == 'POST':
        noticia.titulo = request.form.get('titulo')
        noticia.contenido = request.form.get('contenido')
        noticia.activa = request.form.get('activa') == 'on'
        
        imagen_url = request.form.get('imagen_url')
        imagen_file = request.files.get('imagen_file')
        
        if imagen_file and imagen_file.filename:
            import os
            from flask import current_app
            ext = imagen_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ('jpg', 'jpeg', 'png', 'gif'):
                filename = f"noticia_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'noticias')
                os.makedirs(upload_dir, exist_ok=True)
                imagen_file.save(os.path.join(upload_dir, filename))
                imagen_url = f"/static/uploads/noticias/{filename}"
        
        noticia.imagen_url = imagen_url if imagen_url else None
        db.session.commit()
        flash('Noticia actualizada exitosamente', 'success')
        return redirect(url_for('admin.noticias'))
    
    return render_template('admin/noticia_form.html', noticia=noticia, titulo='Editar Noticia')

@admin_bp.route('/reportes')
@login_required
@admin_required
def reportes():
    return render_template('admin/reportes.html')

@admin_bp.route('/reportes/clientes/pdf')
@login_required
@admin_required
def reporte_clientes_pdf():
    from services.report_service import generate_clientes_pdf
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    buffer = generate_clientes_pdf(clientes)
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename=reporte_clientes.pdf'
    }

@admin_bp.route('/reportes/clientes/excel')
@login_required
@admin_required
def reporte_clientes_excel():
    from services.report_service import generate_clientes_excel
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    buffer = generate_clientes_excel(clientes)
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=reporte_clientes.xlsx'
    }

@admin_bp.route('/reportes/pagos/pdf')
@login_required
@admin_required
def reporte_pagos_pdf():
    from services.report_service import generate_pagos_pdf
    pagos = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    buffer = generate_pagos_pdf(pagos)
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename=reporte_pagos.pdf'
    }

@admin_bp.route('/reportes/pagos/excel')
@login_required
@admin_required
def reporte_pagos_excel():
    from services.report_service import generate_pagos_excel
    pagos = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    buffer = generate_pagos_excel(pagos)
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=reporte_pagos.xlsx'
    }

@admin_bp.route('/clientes/<int:id_cliente>/qr')
@login_required
@admin_required
def cliente_qr(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    qr_data = generate_qr_code(cliente.numero_registro)
    return render_template('admin/cliente_qr.html', cliente=cliente, qr_data=qr_data)

@admin_bp.route('/clientes/<int:id_cliente>/recordatorio', methods=['POST'])
@login_required
@admin_required
def enviar_recordatorio(id_cliente):
    try:
        cliente = Cliente.query.get_or_404(id_cliente)

        default_msg = (
            '¡Hola {nombre}! 💪 Tu membresía {tipo} vence en {días} días '
            '({fecha}). ¡Renueva pronto para seguir entrenando!'
        )

        try:
            config = ConfiguracionRecordatorio.get_config()
            mensaje_template = config.mensaje_recordatorio or default_msg
        except Exception:
            mensaje_template = default_msg

        mensaje = mensaje_template.format(
            nombre=cliente.nickname or cliente.nombre_completo,
            tipo=cliente.tipo_membresia or 'General',
            días=cliente.dias_para_vencer or 0,
            fecha=cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else 'N/A'
        )

        exitoso = send_telegram(mensaje)

        recordatorio = RecordatorioEnviado(
            id_cliente=cliente.id_cliente,
            tipo='manual',
            mensaje=mensaje,
            exitoso=exitoso
        )
        db.session.add(recordatorio)
        db.session.commit()

        if exitoso:
            flash('Recordatorio enviado por Telegram', 'success')
        else:
            flash('Error al enviar. Verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en Railway.', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.clientes'))

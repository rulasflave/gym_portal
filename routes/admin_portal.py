from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models.cliente import Cliente
from models.pago import Pago
from models.noticia import Noticia
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from services.qr_service import generate_qr_code
from extensions import db
from datetime import datetime
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
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    return render_template('admin/clientes.html', clientes=clientes)

def save_photo(file):
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, unique_filename))
        return unique_filename
    return None

@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_cliente():
    if request.method == 'POST':
        numero_registro = request.form.get('numero_registro')
        
        if Cliente.query.filter_by(numero_registro=numero_registro).first():
            flash('El número de registro ya existe', 'error')
            return redirect(url_for('admin.nuevo_cliente'))
        
        password = generate_password_hash('cambiar123')
        
        foto_url = None
        if 'foto' in request.files:
            foto_url = save_photo(request.files['foto'])
        
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
            fecha_inicio_membresia=datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date() if request.form.get('fecha_inicio') else None,
            fecha_fin_membresia=datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date() if request.form.get('fecha_fin') else None,
            estado_membresia='activa',
            usuario_login=numero_registro,
            password_hash=password,
            primer_login=True,
            foto_url=foto_url
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        flash('Cliente creado exitosamente', 'success')
        return redirect(url_for('admin.clientes'))
    
    return render_template('admin/cliente_form.html')

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
        cliente.fecha_inicio_membresia = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date() if request.form.get('fecha_inicio') else None
        cliente.fecha_fin_membresia = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date() if request.form.get('fecha_fin') else None
        
        if 'foto' in request.files and request.files['foto'].filename:
            foto_url = save_photo(request.files['foto'])
            if foto_url:
                cliente.foto_url = foto_url
        
        db.session.commit()
        
        flash('Cliente actualizado', 'success')
        return redirect(url_for('admin.clientes'))
    
    return render_template('admin/cliente_form.html', cliente=cliente)

@admin_bp.route('/pagos')
@login_required
@admin_required
def pagos():
    pagos = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    return render_template('admin/pagos.html', pagos=pagos)

@admin_bp.route('/pagos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_pago():
    if request.method == 'POST':
        id_cliente = request.form.get('id_cliente')
        cliente = Cliente.query.get_or_404(int(id_cliente))
        
        pago = Pago(
            id_cliente=int(id_cliente),
            monto=float(request.form.get('monto', 0)),
            fecha_pago=datetime.strptime(request.form.get('fecha_pago'), '%Y-%m-%d').date(),
            metodo_pago=request.form.get('metodo_pago'),
            concepto=request.form.get('concepto')
        )
        
        db.session.add(pago)
        db.session.commit()
        
        flash('Pago registrado exitosamente', 'success')
        return redirect(url_for('admin.pagos'))
    
    clientes = Cliente.query.order_by(Cliente.numero_registro).all()
    return render_template('admin/pago_form.html', clientes=clientes, today=datetime.now().strftime('%Y-%m-%d'))

@admin_bp.route('/noticias')
@login_required
@admin_required
def noticias():
    noticias = Noticia.query.order_by(Noticia.fecha_publicacion.desc()).all()
    return render_template('admin/noticias.html', noticias=noticias)

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

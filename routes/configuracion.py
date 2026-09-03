from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from extensions import db

config_bp = Blueprint('configuracion', __name__)


@config_bp.route('/admin/configuracion-recordatorios', methods=['GET', 'POST'])
@login_required
def configuracion_recordatorios():
    config = ConfiguracionRecordatorio.get_config()

    if request.method == 'POST':
        config.dias_antes = int(request.form.get('dias_antes', 3))
        config.horario_envio = request.form.get('horario_envio', '09:00')
        config.activo = request.form.get('activo') == 'on'
        config.mensaje_recordatorio = request.form.get('mensaje_recordatorio', '')
        config.chat_ids = request.form.get('chat_ids', '').strip()

        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('configuracion.configuracion_recordatorios'))

    return render_template('admin/configuracion_recordatorios.html', config=config)

from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from models.cliente import Cliente
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from models.recordatorio_enviado import RecordatorioEnviado
from services.notification_service import send_whatsapp
from extensions import db

scheduler = BackgroundScheduler()


def send_reminders():
    with scheduler.app.app_context():
        config = ConfiguracionRecordatorio.get_config()

        if not config.activo:
            return

        target_date = date.today() + timedelta(days=config.dias_antes)

        clientes = Cliente.query.filter(
            Cliente.fecha_fin_membresia == target_date,
            Cliente.activo == True,
            Cliente.telefono.isnot(None)
        ).all()

        for cliente in clientes:
            mensaje = config.mensaje_whatsapp.format(
                nombre=cliente.nickname or cliente.nombre_completo,
                tipo=cliente.tipo_membresia or 'General',
                días=config.dias_antes,
                fecha=cliente.fecha_fin_membresia.strftime('%d/%m/%Y')
            )

            exitoso = send_whatsapp(cliente.telefono, mensaje)

            recordatorio = RecordatorioEnviado(
                id_cliente=cliente.id_cliente,
                tipo='automatico',
                mensaje=mensaje,
                exitoso=exitoso
            )
            db.session.add(recordatorio)

        db.session.commit()


def init_scheduler(app):
    scheduler.app = app

    with app.app_context():
        try:
            config = ConfiguracionRecordatorio.get_config()
            horario = config.horario_envio
        except Exception:
            horario = '09:00'

        hora, minuto = map(int, horario.split(':'))

        scheduler.add_job(send_reminders, 'cron', hour=hora, minute=minuto)
        scheduler.start()

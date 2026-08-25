# WhatsApp Reminder System Design

## Overview
Automatic and manual WhatsApp reminder system for membership expiry notifications.

## Goals
- Send automatic WhatsApp reminders when membership is about to expire
- Allow manual reminders from admin panel
- Configurable reminder days, time, and message

## Components

### 1. Configuration Model
Store reminder settings in database:

```python
class ConfiguracionRecordatorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dias_antes = db.Column(db.Integer, default=3)
    horario_envio = db.Column(db.String(5), default='09:00')
    activo = db.Column(db.Boolean, default=True)
    mensaje_whatsapp = db.Column(db.Text)
```

### 2. Admin Configuration Page
New route: `/admin/configuracion-recordatorios`

Features:
- Set days before expiry (1-30)
- Set send time (HH:MM)
- Enable/disable automatic reminders
- Customize message template
- Preview message

### 3. Automatic Sender
Scheduled task using APScheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'cron', hour=9, minute=0)
scheduler.start()
```

Logic:
1. Run daily at configured time
2. Query clients where `fecha_fin_membresia = today + dias_antes`
3. Send WhatsApp to each
4. Log sent messages in `RecordatorioEnviado` table

### 4. Manual Sender
Button in client list and detail pages:

```
[Recordatorio] → sends immediate WhatsApp
```

### 5. Message Template Variables
- `{nombre}` - Client name or nickname
- `{tipo}` - Membership type
- `{dias}` - Days until expiry
- `{fecha}` - Expiry date (DD/MM/YYYY)

Default message:
```
Hola {nombre}, tu membresía {tipo} vence en {días} días ({fecha}). Acércate a renovar para seguir entrenando. ¡Te esperamos en el gym! 💪
```

### 6. Message Log Table
```python
class RecordatorioEnviado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'))
    tipo = db.Column(db.String(20))  # 'automatico' o 'manual'
    mensaje = db.Column(db.Text)
    enviado_en = db.Column(db.DateTime)
    exitoso = db.Column(db.Boolean)
```

## Files to Create/Modify

### New Files
- `models/configuracion_recordatorio.py`
- `models/recordatorio_enviado.py`
- `routes/configuracion.py`
- `templates/admin/configuracion_recordatorios.html`

### Modified Files
- `models/__init__.py` - import new models
- `routes/admin_portal.py` - add manual send button
- `templates/admin/clientes.html` - add recordatorio button
- `app.py` - initialize scheduler
- `requirements.txt` - add APScheduler
- `services/notification_service.py` - update send_whatsapp

## Environment Variables
```
WHATSAPP_API_KEY=twilio_account_sid
WHATSAPP_API_SECRET=twilio_auth_token
```

## Testing
1. Configure reminder settings
2. Add client with membership expiring in X days
3. Verify automatic send at configured time
4. Test manual send button
5. Check message log in database

## Deployment Notes
- APScheduler runs in background thread
- Works on Railway (single worker)
- No cron job needed on server

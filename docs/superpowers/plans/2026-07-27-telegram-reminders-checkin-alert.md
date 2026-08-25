# Telegram Reminders + Check-in Alert Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace WhatsApp reminders with Telegram-only reminders and add a membership expiry alert on check-in when 3 days or less remain.

**Architecture:** Simplify notification service to use Telegram API (HTTP requests) instead of Twilio. Add check-in alert logic to kiosco validation endpoint that returns expiry warning data. Update templates to display alert popup.

**Tech Stack:** Python, Flask, APScheduler, Telegram Bot API (requests library), Bootstrap 5

## Global Constraints

- Python 3.12 (Railway)
- PostgreSQL (production), SQLite (local dev)
- Flask-Login for authentication
- APScheduler for background jobs
- Telegram Bot API via HTTP requests (no external library needed)

---

## File Structure

| File | Responsibility |
|------|----------------|
| `services/notification_service.py` | Send messages via Telegram API |
| `services/reminder_scheduler.py` | APScheduler job for automatic reminders |
| `routes/configuracion.py` | Admin config page for Telegram settings |
| `routes/kiosco.py` | Check-in validation with expiry alert |
| `models/configuracion_recordatorio.py` | Store Telegram config |
| `templates/admin/configuracion_recordatorios.html` | Config UI |
| `templates/kiosco/scanner.html` | Kiosco UI with alert popup |

---

### Task 1: Update Notification Service for Telegram

**Files:**
- Modify: `services/notification_service.py`

**Interfaces:**
- Consumes: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` env vars
- Produces: `send_telegram(message)` function

- [ ] **Step 1: Replace WhatsApp with Telegram**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests

def send_telegram(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Telegram not configured, skipping message")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram: {e}")
        return False

def send_email(to_email, subject, body):
    # Keep existing email function
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        print("SMTP not configured, skipping email")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
```

- [ ] **Step 2: Update notify functions**

```python
def notify_membresia_venciendo(cliente, dias_restantes):
    subject = f"Tu membresía vence en {dias_restantes} días"
    body = f"""
    <h2>Hola {cliente.nickname or cliente.nombre_completo},</h2>
    <p>Tu membresía vence en <strong>{dias_restantes} días</strong>.</p>
    <p>Fecha de vencimiento: {cliente.fecha_fin_membresia.strftime('%d/%m/%Y')}</p>
    <p>Renueva para seguir disfrutando del gym.</p>
    <p>Saludos,<br>Gym Portal</p>
    """
    
    if cliente.email:
        send_email(cliente.email, subject, body)
    
    message = f"¡Hola {cliente.nickname}! 💪 Tu membresía vence en {dias_restantes} días ({cliente.fecha_fin_membresia.strftime('%d/%m/%Y')}). ¡Renueva pronto para seguir entrenando!"
    send_telegram(message)

def notify_cumpleanos(cliente):
    subject = "¡Feliz cumpleaños! 🎂"
    body = f"""
    <h2>¡Feliz cumpleaños {cliente.nickname or cliente.nombre_completo}!</h2>
    <p>Te deseamos un excelente día.</p>
    <p>Saludos,<br>Gym Portal</p>
    """
    
    if cliente.email:
        send_email(cliente.email, subject, body)
    
    message = f"🎂 ¡Feliz cumpleaños {cliente.nickname}! Te deseamos un excelente día. ¡Te esperamos en el gym!"
    send_telegram(message)
```

- [ ] **Step 3: Commit**

```bash
git add services/notification_service.py
git commit -m "feat: replace WhatsApp with Telegram notifications"
```

---

### Task 2: Update Reminder Scheduler for Telegram

**Files:**
- Rename: `services/whatsapp_scheduler.py` → `services/reminder_scheduler.py`
- Modify: `services/reminder_scheduler.py`

**Interfaces:**
- Consumes: `send_telegram()` from notification_service
- Produces: `init_scheduler(app)` function

- [ ] **Step 1: Create reminder_scheduler.py**

```python
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from models.cliente import Cliente
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from models.recordatorio_enviado import RecordatorioEnviado
from services.notification_service import send_telegram
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
            Cliente.activo == True
        ).all()

        for cliente in clientes:
            mensaje = config.mensaje_recordatorio.format(
                nombre=cliente.nickname or cliente.nombre_completo,
                tipo=cliente.tipo_membresia or 'General',
                días=config.dias_antes,
                fecha=cliente.fecha_fin_membresia.strftime('%d/%m/%Y')
            )

            exitoso = send_telegram(mensaje)

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
```

- [ ] **Step 2: Delete old whatsapp_scheduler.py**

```bash
rm services/whatsapp_scheduler.py
```

- [ ] **Step 3: Commit**

```bash
git add services/reminder_scheduler.py
git rm services/whatsapp_scheduler.py
git commit -m "feat: rename scheduler to reminder_scheduler with Telegram"
```

---

### Task 3: Update Configuration Model

**Files:**
- Modify: `models/configuracion_recordatorio.py`

**Interfaces:**
- Consumes: database
- Produces: `mensaje_recordatorio` field

- [ ] **Step 1: Update model**

```python
from extensions import db


class ConfiguracionRecordatorio(db.Model):
    __tablename__ = 'configuracion_recordatorio'

    id = db.Column(db.Integer, primary_key=True)
    dias_antes = db.Column(db.Integer, default=3)
    horario_envio = db.Column(db.String(5), default='09:00')
    activo = db.Column(db.Boolean, default=True)
    mensaje_recordatorio = db.Column(db.Text, default=(
        '¡Hola {nombre}! 💪 Tu membresía {tipo} vence en {días} días '
        '({fecha}). ¡Renueva pronto para seguir entrenando!'
    ))

    @classmethod
    def get_config(cls):
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config
```

- [ ] **Step 2: Commit**

```bash
git add models/configuracion_recordatorio.py
git commit -m "feat: update config model with mensaje_recordatorio field"
```

---

### Task 4: Update Configuration Route

**Files:**
- Modify: `routes/configuracion.py`

**Interfaces:**
- Consumes: `ConfiguracionRecordatorio` model
- Produces: updated config page

- [ ] **Step 1: Update route**

```python
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

        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('configuracion.configuracion_recordatorios'))

    return render_template('admin/configuracion_recordatorios.html', config=config)
```

- [ ] **Step 2: Commit**

```bash
git add routes/configuracion.py
git commit -m "feat: update config route for Telegram settings"
```

---

### Task 5: Update Configuration Template

**Files:**
- Modify: `templates/admin/configuracion_recordatorios.html`

**Interfaces:**
- Consumes: `config` object
- Produces: updated config UI

- [ ] **Step 1: Update template**

```html
{% extends "base.html" %}
{% block title %}Configuración de Recordatorios{% endblock %}
{% block content %}
<div class="container mt-4">
    <h2><i class="fas fa-cog me-2"></i>Configuración de Recordatorios</h2>

    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %}
    {% endif %}
    {% endwith %}

    <div class="card">
        <div class="card-body">
            <form method="POST">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Días antes del vencimiento</label>
                        <input type="number" name="dias_antes" class="form-control"
                               value="{{ config.dias_antes }}" min="1" max="30">
                        <small class="text-muted">Enviar recordatorio X días antes de vencer</small>
                    </div>

                    <div class="col-md-6 mb-3">
                        <label class="form-label">Horario de envío</label>
                        <input type="time" name="horario_envio" class="form-control"
                               value="{{ config.horario_envio }}">
                        <small class="text-muted">Hora diaria de envío automático</small>
                    </div>
                </div>

                <div class="mb-3 form-check">
                    <input type="checkbox" name="activo" class="form-check-input"
                           {{ 'checked' if config.activo }}>
                    <label class="form-check-label">Envío automático activo</label>
                </div>

                <div class="mb-3">
                    <label class="form-label">Mensaje de recordatorio</label>
                    <textarea name="mensaje_recordatorio" class="form-control" rows="4">{{ config.mensaje_recordatorio }}</textarea>
                    <small class="text-muted">
                        Variables disponibles: <code>{nombre}</code>, <code>{tipo}</code>, <code>{días}</code>, <code>{fecha}</code>
                    </small>
                </div>

                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Telegram:</strong> Los recordatorios se envían al chat ID configurado en las variables de entorno.
                </div>

                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save me-1"></i>Guardar configuración
                </button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/admin/configuracion_recordatorios.html
git commit -m "feat: update config template for Telegram"
```

---

### Task 6: Add Check-in Alert to Kiosco

**Files:**
- Modify: `routes/kiosco.py`

**Interfaces:**
- Consumes: `Cliente` model
- Produces: `dias_restantes` field in JSON response

- [ ] **Step 1: Update kiosco validation**

```python
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
    codigo = request.json.get('codigo')
    
    cliente = Cliente.query.filter_by(numero_registro=codigo).first()
    
    if not cliente:
        return jsonify({
            'status': 'error',
            'message': 'Código no válido. Consulta en recepción.'
        })
    
    if not cliente.is_membresia_activa:
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
    
    hoy = datetime.now().date()
    es_cumple = False
    if cliente.fecha_nacimiento:
        es_cumple = cliente.fecha_nacimiento.month == hoy.month and cliente.fecha_nacimiento.day == hoy.day
    
    # Check if membership expires in 3 days or less
    dias_restantes = None
    alerta_vencimiento = False
    if cliente.fecha_fin_membresia:
        delta = cliente.fecha_fin_membresia - hoy
        dias_restantes = delta.days
        if dias_restantes <= 3:
            alerta_vencimiento = True
    
    return jsonify({
        'status': 'ok',
        'nombre': cliente.nickname or cliente.nombre_completo,
        'nombre_completo': cliente.nombre_completo,
        'numero_registro': cliente.numero_registro,
        'foto_url': f'/static/uploads/{cliente.foto_url}' if cliente.foto_url else None,
        'tipo_membresia': cliente.tipo_membresia,
        'fecha_fin': cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else None,
        'es_cumpleanos': es_cumple,
        'alerta_vencimiento': alerta_vencimiento,
        'dias_restantes': dias_restantes,
        'mensaje': f'¡Feliz cumpleaños {cliente.nickname or cliente.nombre_completo}! 🎂🎉' if es_cumple else f'Bienvenido {cliente.nickname or cliente.nombre_completo}!'
    })
```

- [ ] **Step 2: Commit**

```bash
git add routes/kiosco.py
git commit -m "feat: add membership expiry alert on check-in"
```

---

### Task 7: Add Alert Popup to Scanner Template

**Files:**
- Modify: `templates/kiosco/scanner.html`

**Interfaces:**
- Consumes: `alerta_vencimiento`, `dias_restantes` from API
- Produces: alert popup UI

- [ ] **Step 1: Add alert modal HTML**

Add after the welcome overlay div (before the `<style>` tag):

```html
<!-- EXPIRY ALERT MODAL -->
<div id="alerta-vencimiento" style="display: none;">
    <div class="alerta-screen">
        <div class="alerta-content">
            <div class="alerta-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h2 class="alerta-titulo">¡Atención!</h2>
            <p id="alerta-mensaje" class="alerta-mensaje"></p>
            <div class="alerta-badge">
                <i class="fas fa-calendar me-2"></i>
                <span id="alerta-dias"></span>
            </div>
            <p class="alerta-accion">Acércate a recepción para renovar</p>
            <button class="btn btn-lg px-5 py-3 mt-4" onclick="closeAlerta()" 
                    style="background-color: #f5c518; color: #1a1a1a; font-size: 1.2rem; font-weight: bold; border-radius: 15px;">
                <i class="fas fa-check me-2"></i>ENTENDIDO
            </button>
        </div>
    </div>
</div>
```

- [ ] **Step 2: Add CSS styles**

Add to the `<style>` section:

```css
.alerta-screen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.5s ease;
}

.alerta-content {
    text-align: center;
    color: white;
    padding: 2rem;
    max-width: 500px;
}

.alerta-icon {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 1.5s infinite;
    box-shadow: 0 0 50px rgba(255, 107, 107, 0.5);
}

.alerta-icon i {
    font-size: 4rem;
    color: white;
}

.alerta-titulo {
    font-size: 2.5rem;
    font-weight: 800;
    color: #ff6b6b;
    margin-bottom: 1rem;
}

.alerta-mensaje {
    font-size: 1.3rem;
    color: rgba(255,255,255,0.9);
    margin-bottom: 1.5rem;
}

.alerta-badge {
    display: inline-block;
    background: rgba(255, 107, 107, 0.2);
    border: 2px solid #ff6b6b;
    padding: 0.75rem 1.5rem;
    border-radius: 50px;
    font-size: 1.2rem;
    color: #ff6b6b;
    font-weight: 600;
    margin-bottom: 1rem;
}

.alerta-accion {
    font-size: 1.1rem;
    color: rgba(255,255,255,0.7);
    font-style: italic;
}
```

- [ ] **Step 3: Add JavaScript function**

Add to the `<script>` section:

```javascript
function showAlerta(data) {
    const modal = document.getElementById('alerta-vencimiento');
    document.getElementById('alerta-mensaje').textContent = 
        `Tu membresía está por vencer. ¡Renueva pronto!`;
    document.getElementById('alerta-dias').textContent = 
        `${data.dias_restantes} día${data.dias_restantes !== 1 ? 's' : ''} restante${data.dias_restantes !== 1 ? 's' : ''}`;
    modal.style.display = 'block';
}

function closeAlerta() {
    document.getElementById('alerta-vencimiento').style.display = 'none';
}
```

Update the `showWelcome` function to check for alert:

```javascript
function showWelcome(data) {
    // ... existing code ...
    
    // Show expiry alert if applicable
    if (data.alerta_vencimiento) {
        setTimeout(() => {
            showAlerta(data);
        }, 5000); // Show after welcome screen closes
    }
}
```

- [ ] **Step 4: Commit**

```bash
git add templates/kiosco/scanner.html
git commit -m "feat: add expiry alert popup to kiosco scanner"
```

---

### Task 8: Update app.py Import

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: `init_scheduler` from reminder_scheduler
- Produces: updated app initialization

- [ ] **Step 1: Update import**

Find and replace:
```python
from services.whatsapp_scheduler import init_scheduler
```

With:
```python
from services.reminder_scheduler import init_scheduler
```

- [ ] **Step 2: Commit**

```bash
git add app.py
git commit -m "feat: update app.py to use reminder_scheduler"
```

---

### Task 9: Add requests to requirements.txt

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: none
- Produces: updated dependencies

- [ ] **Step 1: Add requests library**

Add to requirements.txt:
```
requests==2.31.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat: add requests library for Telegram API"
```

---

### Task 10: Deploy and Test

**Files:**
- None (deployment only)

**Interfaces:**
- Consumes: all previous tasks
- Produces: working deployment

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Set environment variables in Railway**

```
TELEGRAM_BOT_TOKEN=8078506015:AAEnFjLBMi2eM91lt_BJV8jNrATJu7b4PIw
TELEGRAM_CHAT_ID=665029832
```

- [ ] **Step 3: Test Telegram reminder**

1. Go to `/admin/configuracion-recordatorios`
2. Set "Días antes del vencimiento" to a number that matches a client's expiry
3. Enable "Envío automático activo"
4. Save configuration
5. Wait for scheduled time or test manually

- [ ] **Step 4: Test check-in alert**

1. Go to `/kiosco`
2. Scan a client QR or enter code manually
3. If client has ≤3 days remaining, alert popup should appear

- [ ] **Step 5: Verify deployment**

```bash
curl https://web-production-e64f4.up.railway.app/kiosco
```

Expected: Scanner page loads successfully

# WhatsApp Reminder System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automatic and manual WhatsApp reminder system for membership expiry notifications.

**Architecture:** APScheduler runs daily to send WhatsApp reminders to clients whose membership expires in X days. Admin can configure settings and send manual reminders.

**Tech Stack:** Python, Flask, SQLAlchemy, APScheduler, Twilio WhatsApp API

## Global Constraints
- Python 3.12 (Railway)
- PostgreSQL (production), SQLite (local dev)
- Flask-Login for auth
- User IDs prefixed (`cliente-1`, `admin-1`)
- All routes under `/admin` require admin login

---

### Task 1: Create Configuration Model

**Files:**
- Create: `models/configuracion_recordatorio.py`
- Modify: `models/__init__.py`

**Interfaces:**
- Consumes: `extensions.db`
- Produces: `ConfiguracionRecordatorio` model class

- [ ] **Step 1: Create configuration model**

```python
# models/configuracion_recordatorio.py
from extensions import db

class ConfiguracionRecordatorio(db.Model):
    __tablename__ = 'configuracion_recordatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    dias_antes = db.Column(db.Integer, default=3)
    horario_envio = db.Column(db.String(5), default='09:00')
    activo = db.Column(db.Boolean, default=True)
    mensaje_whatsapp = db.Column(db.Text, default=(
        'Hola {nombre}, tu membresía {tipo} vence en {días} días '
        '({fecha}). Acércate a renovar para seguir entrenando. '
        '¡Te esperamos en el gym! 💪'
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

- [ ] **Step 2: Update models/__init__.py**

Add import:
```python
from models.configuracion_recordatorio import ConfiguracionRecordatorio
```

- [ ] **Step 3: Create migration and apply**

Run: `flask db migrate -m "add configuracion_recordatorio"`
Run: `flask db upgrade`

- [ ] **Step 4: Commit**

```bash
git add models/configuracion_recordatorio.py models/__init__.py
git commit -m "feat: add ConfiguracionRecordatorio model"
```

---

### Task 2: Create Message Log Model

**Files:**
- Create: `models/recordatorio_enviado.py`
- Modify: `models/__init__.py`

**Interfaces:**
- Consumes: `extensions.db`, `Cliente` model
- Produces: `RecordatorioEnviado` model class

- [ ] **Step 1: Create log model**

```python
# models/recordatorio_enviado.py
from datetime import datetime, timezone
from extensions import db

class RecordatorioEnviado(db.Model):
    __tablename__ = 'recordatorios_enviados'
    
    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'automatico' o 'manual'
    mensaje = db.Column(db.Text, nullable=False)
    enviado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    exitoso = db.Column(db.Boolean, default=False)
    
    cliente = db.relationship('Cliente', backref='recordatorios')
```

- [ ] **Step 2: Update models/__init__.py**

Add import:
```python
from models.recordatorio_enviado import RecordatorioEnviado
```

- [ ] **Step 3: Create migration and apply**

Run: `flask db migrate -m "add recordatorios_enviados"`
Run: `flask db upgrade`

- [ ] **Step 4: Commit**

```bash
git add models/recordatorio_enviado.py models/__init__.py
git commit -m "feat: add RecordatorioEnviado model"
```

---

### Task 3: Create Configuration Route and Template

**Files:**
- Create: `routes/configuracion.py`
- Create: `templates/admin/configuracion_recordatorios.html`
- Modify: `app.py`

**Interfaces:**
- Consumes: `ConfiguracionRecordatorio` model, `login_required`
- Produces: GET/POST routes for configuration

- [ ] **Step 1: Create configuration route**

```python
# routes/configuracion.py
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
        config.mensaje_whatsapp = request.form.get('mensaje_whatsapp', '')
        
        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('configuracion.configuracion_recordatorios'))
    
    return render_template('admin/configuracion_recordatorios.html', config=config)
```

- [ ] **Step 2: Create configuration template**

```html
<!-- templates/admin/configuracion_recordatorios.html -->
{% extends "base.html" %}
{% block title %}Configuración de Recordatorios{% endblock %}
{% block content %}
<div class="container mt-4">
    <h2>Configuración de Recordatorios</h2>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %}
    {% endif %}
    {% endwith %}
    
    <form method="POST">
        <div class="mb-3">
            <label class="form-label">Días antes del vencimiento</label>
            <input type="number" name="dias_antes" class="form-control" 
                   value="{{ config.dias_antes }}" min="1" max="30">
        </div>
        
        <div class="mb-3">
            <label class="form-label">Horario de envío</label>
            <input type="time" name="horario_envio" class="form-control" 
                   value="{{ config.horario_envio }}">
        </div>
        
        <div class="mb-3 form-check">
            <input type="checkbox" name="activo" class="form-check-input" 
                   {{ 'checked' if config.activo }}>
            <label class="form-check-label">Activo</label>
        </div>
        
        <div class="mb-3">
            <label class="form-label">Mensaje WhatsApp</label>
            <textarea name="mensaje_whatsapp" class="form-control" rows="4">{{ config.mensaje_whatsapp }}</textarea>
            <small class="text-muted">
                Variables: {nombre}, {tipo}, {días}, {fecha}
            </small>
        </div>
        
        <button type="submit" class="btn btn-primary">Guardar</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 3: Register blueprint in app.py**

Add to `app.py`:
```python
from routes.configuracion import config_bp
app.register_blueprint(config_bp)
```

- [ ] **Step 4: Commit**

```bash
git add routes/configuracion.py templates/admin/configuracion_recordatorios.html app.py
git commit -m "feat: add configuration page for reminders"
```

---

### Task 4: Create Automatic Sender Service

**Files:**
- Create: `services/whatsapp_scheduler.py`
- Modify: `app.py`

**Interfaces:**
- Consumes: `ConfiguracionRecordatorio`, `Cliente`, `RecordatorioEnviado`, `send_whatsapp`
- Produces: `init_scheduler()` function

- [ ] **Step 1: Create scheduler service**

```python
# services/whatsapp_scheduler.py
from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from models.cliente import Cliente
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from models.recordatorio_enviado import RecordatorioEnviado
from services.notification_service import send_whatsapp
from extensions import db

scheduler = BackgroundScheduler()

def send_reminders():
    with db.app.app_context():
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
    global db
    db = app.db
    
    horario = ConfiguracionRecordatorio.get_config().horario_envio
    hora, minuto = map(int, horario.split(':'))
    
    scheduler.add_job(send_reminders, 'cron', hour=hora, minute=minuto)
    scheduler.start()
```

- [ ] **Step 2: Initialize scheduler in app.py**

Add to `app.py` after app creation:
```python
from services.whatsapp_scheduler import init_scheduler
init_scheduler(app)
```

- [ ] **Step 3: Add APScheduler to requirements.txt**

Add line:
```
APScheduler==3.10.4
```

- [ ] **Step 4: Commit**

```bash
git add services/whatsapp_scheduler.py app.py requirements.txt
git commit -m "feat: add automatic WhatsApp scheduler"
```

---

### Task 5: Add Manual Send Button

**Files:**
- Modify: `routes/admin_portal.py`
- Modify: `templates/admin/clientes.html`

**Interfaces:**
- Consumes: `send_whatsapp`, `RecordatorioEnviado`, `ConfiguracionRecordatorio`
- Produces: POST route `/admin/cliente/<id>/recordatorio`

- [ ] **Step 1: Add manual send route**

Add to `routes/admin_portal.py`:
```python
@app.route('/admin/cliente/<int:id_cliente>/recordatorio', methods=['POST'])
@login_required
def enviar_recordatorio(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    config = ConfiguracionRecordatorio.get_config()
    
    if not cliente.telefono:
        flash('El cliente no tiene teléfono registrado', 'warning')
        return redirect(url_for('admin_portal.ver_cliente', id_cliente=id_cliente))
    
    mensaje = config.mensaje_whatsapp.format(
        nombre=cliente.nickname or cliente.nombre_completo,
        tipo=cliente.tipo_membresia or 'General',
        días=cliente.dias_para_vencer or 0,
        fecha=cliente.fecha_fin_membresia.strftime('%d/%m/%Y') if cliente.fecha_fin_membresia else 'N/A'
    )
    
    exitoso = send_whatsapp(cliente.telefono, mensaje)
    
    recordatorio = RecordatorioEnviado(
        id_cliente=cliente.id_cliente,
        tipo='manual',
        mensaje=mensaje,
        exitoso=exitoso
    )
    db.session.add(recordatorio)
    db.session.commit()
    
    if exitoso:
        flash('Recordatorio enviado exitosamente', 'success')
    else:
        flash('Error al enviar recordatorio', 'danger')
    
    return redirect(url_for('admin_portal.ver_cliente', id_cliente=id_cliente))
```

- [ ] **Step 2: Add imports**

Add to top of `routes/admin_portal.py`:
```python
from models.configuracion_recordatorio import ConfiguracionRecordatorio
from models.recordatorio_enviado import RecordatorioEnviado
from services.notification_service import send_whatsapp
```

- [ ] **Step 3: Add button to client detail template**

Add to `templates/admin/cliente_detalle.html` after other action buttons:
```html
<form method="POST" action="{{ url_for('admin_portal.enviar_recordatorio', id_cliente=cliente.id_cliente) }}" style="display:inline">
    <button type="submit" class="btn btn-warning btn-sm" onclick="return confirm('¿Enviar recordatorio?')">
        📱 Recordatorio
    </button>
</form>
```

- [ ] **Step 4: Commit**

```bash
git add routes/admin_portal.py templates/admin/cliente_detalle.html
git commit -m "feat: add manual WhatsApp reminder button"
```

---

### Task 6: Add Navigation Link

**Files:**
- Modify: `templates/base.html`

**Interfaces:**
- Consumes: None
- Produces: Navigation link to configuration page

- [ ] **Step 1: Add nav link**

Add to admin navigation in `templates/base.html`:
```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('configuracion.configuracion_recordatorios') }}">
        📱 Recordatorios
    </a>
</li>
```

- [ ] **Step 2: Commit**

```bash
git add templates/base.html
git commit -m "feat: add reminders navigation link"
```

---

### Task 7: Test Locally

**Files:**
- None (testing only)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified working system

- [ ] **Step 1: Run migrations**

```bash
flask db upgrade
```

- [ ] **Step 2: Start app**

```bash
flask run
```

- [ ] **Step 3: Test configuration page**

1. Login as admin
2. Go to `/admin/configuracion-recordatorios`
3. Change settings and save

- [ ] **Step 4: Test manual send**

1. Go to a client detail page
2. Click "Recordatorio" button
3. Verify message sent (check Twilio logs)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: test reminder system"
```

---

### Task 8: Deploy to Railway

**Files:**
- None (deployment only)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Working system in production

- [ ] **Step 1: Set environment variables in Railway**

```
WHATSAPP_API_KEY=<twilio_account_sid>
WHATSAPP_API_SECRET=<twilio_auth_token>
```

- [ ] **Step 2: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 3: Verify deployment**

1. Check Railway logs for scheduler start
2. Test configuration page
3. Test manual send

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: deploy reminder system to Railway"
```

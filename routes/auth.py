from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.cliente import Cliente
from models.admin import Admin
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password')
        
        cliente = Cliente.query.filter_by(usuario_login=usuario.upper()).first()
        if cliente and check_password_hash(cliente.password_hash, password):
            login_user(cliente)
            if cliente.primer_login:
                return redirect(url_for('cliente.cambiar_password'))
            return redirect(url_for('cliente.dashboard'))
        
        admin = Admin.query.filter_by(email=usuario.lower()).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        
        flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

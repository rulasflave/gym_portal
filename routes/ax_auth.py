from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from routes.auth import authenticate, redirect_after_login

ax_auth_bp = Blueprint('ax_auth', __name__)


@ax_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, tipo = authenticate(
            request.form.get('usuario', '').strip(), request.form.get('password'))
        if user:
            login_user(user)
            return redirect(redirect_after_login(user, tipo))
        flash('Usuario o contraseña incorrectos', 'error')

    return render_template('axis_login.html')


@ax_auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('ax_auth.login'))
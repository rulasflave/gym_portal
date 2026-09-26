from flask import Blueprint, render_template

vitelas_public_bp = Blueprint('vitelas_public', __name__)

@vitelas_public_bp.route('/')
def index():
    return render_template('vitelas_public/index.html')

@vitelas_public_bp.route('/reglamentos')
def reglamentos():
    return render_template('vitelas_public/reglamentos.html')
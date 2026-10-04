from flask import Blueprint, render_template

ax_public_bp = Blueprint('ax_public', __name__)

@ax_public_bp.route('/')
def index():
    return render_template('ax_public/index.html')
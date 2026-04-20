from flask import Blueprint, render_template
from app.models import User

main_bp = Blueprint('main', __name__)

@main_bp.get('/')
def index():
    return render_template('index.html')
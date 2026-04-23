from flask import Blueprint, render_template, session, request
from flask_login import current_user, login_user
from app.services import UserSvc, ListSvc


main_bp = Blueprint('main', __name__)


@main_bp.before_app_request
def guest_handler():
    endpoint = request.endpoint or ""

    if endpoint.endswith('static'):
        return

    if not current_user.is_authenticated:
        guest_user, guest_uuid = UserSvc.create_guest()
        session['guest_uuid'] = guest_uuid
        login_user(guest_user)


@main_bp.get('/')
def index():
    user_lists = current_user.authored_lists
    return render_template(
        'index.html',
        user_lists=user_lists
    )


@main_bp.post('/create-list')
def create_list():
    data = request.get_json()
    title = data.get('title')

    try:
        new_list = ListSvc.create_list(current_user, title)
        return render_template(
            'components/new-task.html',
            new_list=new_list,
        )
    except ValueError as e:
        return {"error": str(e)}, 400
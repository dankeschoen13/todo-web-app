from flask import Blueprint, request, render_template, jsonify, session
from flask_login import login_user, current_user, logout_user
from app.services import UserSvc, DuplicateUserError
from app.services.user_svc import AuthenticationError

auth_bp = Blueprint("auth", __name__)

@auth_bp.before_app_request
def guest_user_handler():
    endpoint = request.endpoint or ""

    if endpoint.endswith('static'):
        return

    if not current_user.is_authenticated:
        guest_user, guest_uuid = UserSvc.create_guest()
        session['guest_uuid'] = guest_uuid
        login_user(guest_user)


@auth_bp.get('/register')
def register_page():
    return render_template('register.html')


@auth_bp.post('/api/register')
def api_register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    try:
        new_user = UserSvc.create_new_user(email, username, password)
        login_user(new_user)
        return jsonify({"message": "User created successfully"}), 201

    except DuplicateUserError as e:
        return jsonify({
            "error": str(e),
            "field": e.field_name
        }), 400

    except ValueError as e:
        return jsonify({"error": str(e), "field": "global"}), 500


@auth_bp.route('/login')
def login_page():
    return render_template('login.html')


@auth_bp.get('/api/login')
def api_login():
    data = request.json()
    login_identifier = data.get('identifier')
    password = data.get('password')

    try:
        user = UserSvc.authenticate_user(login_identifier, password)
        login_user(user)
        return jsonify({"message": "User logged in successfully"}), 201

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401


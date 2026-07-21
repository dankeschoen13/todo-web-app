from flask import Blueprint, request, render_template, jsonify, session, flash, redirect, url_for, g
from flask_login import login_user, current_user, logout_user
from app.services import UserSvc, DuplicateUserError
from app.services.user_svc import AuthenticationError

auth_bp = Blueprint("auth", __name__)

@auth_bp.before_app_request
def guest_user_handler():

    if (request.endpoint or "").endswith('static'):
        return

    if current_user.is_authenticated:
        g.current_user_id = current_user.id
    else:
        g.current_user_id = None

@auth_bp.get('/register')
def register_page():
    if current_user.is_authenticated and not current_user.is_guest:
        flash('You are already logged in!', 'info')
        return redirect(url_for('main.index'))

    return render_template('register.html')


@auth_bp.post('/api/register')
def api_register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    guest_uuid = session.get('guest_uuid')
    existing_guest = None

    if isinstance(guest_uuid, str):
        existing_guest = UserSvc.fetch_guest_by_uuid(guest_uuid)

    try:
        new_user = UserSvc.create_user(email, username, password, existing_guest)

    except DuplicateUserError as e:
        return jsonify({
            "error": str(e), "field": e.field_name
        }), 400

    except ValueError as e:
        return jsonify({
            "error": str(e), "field": "global"
        }), 500

    session.pop('guest_uuid', None)
    login_user(new_user)
    return jsonify({"message": "User created successfully"}), 201


@auth_bp.get('/login')
def login_page():
    if current_user.is_authenticated and not current_user.is_guest:
        flash('You are already logged in', 'info')
        return redirect(url_for('main.index'))

    return render_template('login.html')


@auth_bp.post('/api/login')
def api_login():
    data = request.get_json()
    login_identifier = data.get('identifier')
    password = data.get('password')

    try:
        user = UserSvc.authenticate_user(login_identifier, password)

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401

    session.pop('guest_uuid', None)
    login_user(user)
    return jsonify({"message": "User logged in successfully"}), 200


@auth_bp.get('/logout')
def logout():
    if current_user.is_authenticated and not current_user.is_guest:
        logout_user()
        flash('You have been logged out', 'info')

        next_page = request.args.get('next')
        if next_page:
            return redirect(url_for(next_page))

    return redirect(url_for('web.index'))
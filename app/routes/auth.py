from flask import Blueprint, request, render_template, jsonify
from app.services import UserSvc, DuplicateUserError

auth_bp = Blueprint("auth", __name__)

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
        return jsonify({"message": "User created successfully"}), 201

    except DuplicateUserError as e:
        return jsonify({
            "error": str(e),
            "field": e.field_name
        }), 400

    except ValueError as e:
        return jsonify({"error": str(e), "field": "global"}), 500


@auth_bp.route('/login')
def login():
    return render_template('login.html')
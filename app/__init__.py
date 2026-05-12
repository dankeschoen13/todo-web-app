from flask import Flask
from config import Config
from app.extensions import db, migrate, csrf, login_manager

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db) # render_as_batch=True if SQLite
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.routes import main_bp, auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
from flask import Flask, render_template
from flask_login import LoginManager

from app.db import db

def create_app(test_config=False):
    # initialize flask app
    app = Flask(__name__)
    app.config["TESTING"] = test_config

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "supersecretkey"

    # Initialize extensions with app
    db.init_app(app)

    from .models import User, Role
    from .config.seeding import seed_roles, seed_users, seed_patient_assessments

    with app.app_context():
        db.drop_all() # for development
        db.create_all()
        seed_roles()
        seed_users()
        seed_patient_assessments()

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .memory_test import memory_test as memory_test_blueprint
    app.register_blueprint(memory_test_blueprint, url_prefix='/assessments/memory_test')

    # handle 403 error
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app

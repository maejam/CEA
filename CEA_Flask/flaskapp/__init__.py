import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail

from .db import init_db
from config import config


# Create extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
bootstrap = Bootstrap()
mail = Mail()

from .db import init_db

def create_app(config_name=None):
    """ App factory """
    if config_name is None:
        config_name = os.environ.get("APP_CONFIG", "development")

    # Create and configure app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.url_map.strict_slashes = False

    # Initialize database
    DB_CONN_STR = app.config["DB_CONN_STR"]
    DB_NAME = app.config["DB_NAME"]
    init_db(DB_CONN_STR, DB_NAME)

    # Register extensions
    bcrypt.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    bootstrap.init_app(app)

    mail.init_app(app)

    # Register Blueprints
    from .app import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    return app


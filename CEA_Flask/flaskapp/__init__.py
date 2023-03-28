from .db import init_db, MongoAPI
import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_mail import Mail


from config import config


# Create extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
bootstrap = Bootstrap()
mail = Mail()


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

    # Initialize API for handle linkedin scrapper posts
    client_api = MongoAPI(DB_CONN_STR, DB_NAME, data)

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

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app

import os


class Config():
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY",
                                "2403b10a2baad99dad060f06e01a711d418378f7a6f31f29e5f2db0376964165")

    DB_CONN_STR = os.environ.get("DB_CONN_STR", "mongodb://mongo:27017")
    DB_NAME = os.environ.get("DB_NAME", "CEA")

    MAIL_SERVER = "smtp.office365.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "cfrmsbd2223@outlook.fr"
    MAIL_PASSWORD = "Bep2jh9AfKWu6AJ"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


class TestingConfig(Config):
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
    }

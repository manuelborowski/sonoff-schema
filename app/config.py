DB_TOOLS = False


class Config(object):
    STATIC_PATH = "app/static"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "INFO"
    PRESERVE_CONTEXT_ON_EXCEPTION = True
    SOCKETIO_ASYNC_MODE = 'eventlet'

class DevelopmentConfig(Config):
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
    }

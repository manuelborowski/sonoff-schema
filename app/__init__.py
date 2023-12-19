from peewee import SqliteDatabase
import logging, logging.handlers, os, sys
from flask import Flask
from flask_socketio import SocketIO

# 0.1: initial version
# 0.2: second version
# 0.3: introduced arbitrary events to update cells
# 0.4: added logging.  Implemented scheduler and sonoff-loop
# 0.5: bugfix in mqtt start
# 0.6: bugfix in mqtt start

version = "0.6"

#  enable logging
top_log_handle = "sonoff"
log = logging.getLogger(f"{top_log_handle}.{__name__}")
LOG_FILENAME = os.path.join(sys.path[0], f'app/static/log/sonoff.txt')
log_level = getattr(logging, 'INFO')
log.setLevel(log_level)
log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)


app = Flask(__name__, instance_relative_config=True, template_folder='presentation/template/')

log.info("START sonoff-schema")

from app.config import app_config
config_name = os.getenv('FLASK_CONFIG')
config_name = config_name if config_name else 'production'
app.config.from_object(app_config[config_name])
app.config.from_pyfile('config.py')


app.config.from_mapping(DATABASE=os.path.join(app.instance_path, app.config["DATABASE_FILE"]),)
socketio = SocketIO(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'], cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGIN'])

# from app.data import db
# db.init_app(app)

dbase = SqliteDatabase(app.config["DATABASE"])
dbase.close()
# import app.data

from .presentation.view import index
app.register_blueprint(index.bp)

from .application.scheduler import scheduler_start
scheduler_start(dbase)


def populate_database():
    from app.data.scheme import Scheme
    Scheme(gid=1).save()
    Scheme(gid=1).save()
    Scheme(gid=2).save()
    Scheme(gid=2).save()
    Scheme(gid=3).save()
    Scheme(gid=3).save()
    Scheme(gid=4).save()
    Scheme(gid=4).save()

    from app.data.sonoff import Sonoff
    Sonoff().save()
    Sonoff().save()
    Sonoff().save()
    Sonoff().save()


# populate_database()


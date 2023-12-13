from peewee import SqliteDatabase
import os
from flask import Flask
from flask_socketio import SocketIO

# 0.1: initial version

app = Flask(__name__, instance_relative_config=True, template_folder='presentation/template/')

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
    Sonoff(sonoff_id="sonoff1", location="kegel", schemes=[2]).save()
    Sonoff(sonoff_id="sonoff2", location="boom", schemes=[2, 3]).save()
    Sonoff(sonoff_id="sonoff3", location="buiten", schemes=[1, 2]).save()


# populate_database()


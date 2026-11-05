from peewee import SqliteDatabase
import logging.handlers, os
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO

# 0.1: initial version
# 0.2: second version
# 0.3: introduced arbitrary events to update cells
# 0.4: added logging.  Implemented scheduler and sonoff-loop
# 0.5: bugfix in mqtt start
# 0.6: bugfix in mqtt start
# 0.7: esthetic updates
# 0.8: hide index
# 0.9: code cleanup.  Setting state of sonoff-device is commented out.
# 0.10: split mode and active so that it is possible to switch a sonoff on or off while the scheduler is active.
# 0.11: add favicon to git
# 0.12: css update
# 0.13: bugfixed socketio, used eventlet iso gevent
# 0.14: decoupled sonoff button from relay.  Pushing the button on the sonoff, pushing the button in the GUI or switching in a scheme (if appropriate) will toggle the 'active'-property.
# 0.15: update frontend

version = "0.15"

#  enable logging
top_log_handle = "sonoff"
log = logging.getLogger(f"{top_log_handle}.{__name__}")
LOG_FILENAME = Path(__file__).resolve().parents[1] / 'log' / 'sonoff.txt'
LOG_FILENAME.parent.mkdir(parents=True, exist_ok=True)
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
# socketio = SocketIO(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'], cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGIN'])
socketio = SocketIO(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'])

dbase = SqliteDatabase(app.config["DATABASE"])

from .data.scheme import Scheme
from .data.sonoff import Sonoff

with dbase.connection_context(), dbase.atomic("IMMEDIATE"):
    if not Sonoff.table_exists():
        Sonoff.create_table()
        Sonoff.insert_many([{"schemes": []} for _ in range(4)]).execute()
    if not Scheme.table_exists():
        Scheme.create_table()
        Scheme.insert_many([{"gid": gid} for gid in range(1, 5) for _ in range(2)]).execute()

from .presentation.view import index
app.register_blueprint(index.bp)


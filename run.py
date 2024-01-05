from app import app, socketio, dbase
from app.application.scheduler import scheduler_start

if __name__ == '__main__':
    scheduler_start(dbase)
    socketio.run(app, port=app.config['FLASK_PORT'], host=app.config['FLASK_IP'])

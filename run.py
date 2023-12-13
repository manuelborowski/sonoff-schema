from app import app, socketio

if __name__ == '__main__':
    socketio.run(app, port=app.config['FLASK_PORT'], host=app.config['FLASK_IP'])

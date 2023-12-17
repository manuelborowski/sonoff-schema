import threading, datetime, time
from app.data.sonoff import Sonoff
from app.data.scheme import Scheme
from app import socketio, app
from flask_socketio import send

def scheduler_task(db):
    with app.app_context():
        state = True

        while True:
            print(datetime.datetime.now(), db)
            db.connect()
            schemes = Scheme.select().where(Scheme.active==True)
            print([(s.id, s.gid) for s in schemes])
            db.close()
            send({"id": f"sonoffstate-1", "value": state}, json=True, broadcast=True, namespace=f"/sonoffupdate")
            state = not state
            time.sleep(2)


def scheduler_start(db):
    scheduler = threading.Thread(target=scheduler_task, args=[db])
    scheduler.start()


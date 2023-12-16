import threading, datetime, time
from app.data.sonoff import Sonoff
from app.data.scheme import Scheme

def scheduler_task(db):
    while True:
        print(datetime.datetime.now(), db)
        db.connect()
        schemes = Scheme.select().where(Scheme.active==True)
        print([(s.id, s.gid) for s in schemes])
        db.close()
        time.sleep(2)


def scheduler_start(db):
    scheduler = threading.Thread(target=scheduler_task, args=[db])
    scheduler.start()


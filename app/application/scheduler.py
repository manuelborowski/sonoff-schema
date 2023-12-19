from peewee import DoesNotExist
import threading, datetime, time
from app.data.sonoff import Sonoff
from app.data.scheme import Scheme
from app import socketio, app
from flask_socketio import send
from app.data.mqtt import Tasmota


#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

sonoff_sonoff_ids = {}
sonoff_ids = {}
currrent_sonoffs = []

def set_sonoff_state_cb(sonoff_id, status):
    try:
        with app.app_context():
            if sonoff_id in sonoff_sonoff_ids:
                send({"id": f"sonoffstate-{sonoff_sonoff_ids[sonoff_id].id}", "value": status}, json=True, broadcast=True, namespace=f"/sonoffupdate")
    except DoesNotExist as e:
        return False


def set_sonoff_ip_cb(sonoff_id, ip):
    try:
        with app.app_context():
            if sonoff_id in sonoff_sonoff_ids:
                send({"id": f"sonoffip-{sonoff_sonoff_ids[sonoff_id].id}", "value": ip}, json=True, broadcast=True, namespace=f"/sonoffupdate")
    except DoesNotExist as e:
        return False


tasmota = Tasmota(app, log, set_sonoff_state_cb, set_sonoff_ip_cb)


def scheduler_task(db):
    global sonoff_sonoff_ids
    global sonoff_ids
    days_of_week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    onoff_template = [["on0", True], ["off0", False], ["on1", True], ["off1", False]]
    with app.app_context():
        state = True
        valid_sonoffs = []
        while True:
            try:
                # log.info(datetime.datetime.now())
                temp_sonoffs = []
                db.connect()
                sonoffs = Sonoff.select().where(Sonoff.sonoff_id != "")
                sonoff_sonoff_ids = {s.sonoff_id: s for s in sonoffs}
                sonoff_ids = {s.id: s for s in sonoffs}
                for sonoff in sonoffs:
                    # tasmota.request_status(sonoff.sonoff_id)
                    if sonoff.sonoff_id not in valid_sonoffs:
                        tasmota.subscribe_to_switch(sonoff.sonoff_id)
                        valid_sonoffs.append(sonoff.sonoff_id)
                    temp_sonoffs.append(sonoff.sonoff_id)
                not_valid_sonoffs = list(set(valid_sonoffs) ^ set(temp_sonoffs))
                valid_sonoffs = list(set(valid_sonoffs) ^ set(not_valid_sonoffs))
                for sonoff_id in not_valid_sonoffs:
                     tasmota.unsubscribe_from_switch(sonoff_id)
                for sonoff_id in valid_sonoffs:
                    tasmota.request_status(sonoff_id)

                now = datetime.datetime.now()
                reference_time = f"{int(now.hour):02d}:{int(now.minute):02d}"
                update_schemes = {}
                schemes = Scheme.select().where(Scheme.active==True, getattr(Scheme, days_of_week[now.weekday()])==True)
                for scheme in schemes:
                    for onoff in onoff_template:
                        property = getattr(scheme, onoff[0])
                        if property != "":
                            h, m = property.split(":")
                            property_time = f"{int(h):02d}:{int(m):02d}"
                            if property_time <= reference_time:
                                if scheme.gid not in update_schemes or property_time > update_schemes[scheme.gid]["time"]:
                                    update_schemes[scheme.gid] = {"time": property_time, "action": onoff[1]}
                update_sonoffs = {}
                for sonoff in sonoffs:
                    if sonoff.mode == Sonoff.State.auto:
                        for gid in sonoff.schemes:
                            if gid in update_schemes:
                                update_sonoffs[sonoff.sonoff_id] = update_schemes[gid]["action"]
                for id, state in update_sonoffs.items():
                    tasmota.set_switch_state(id, state)

                #     ip = tasmota.get_switch_ip(sonoff.sonoff_id)
                #     log.info(ip)
                # #     ip = datetime.datetime.now()
                #     send({"id": f"sonoffip-{sonoff.id}", "value": ip}, json=True, broadcast=True, namespace=f"/sonoffupdate")
                state = not state
                db.close()
                # tasmota.hb_timer_tick()
                time.sleep(2)
            except Exception as e:
                log.error(f"task error, {e}")


def set_sonoff_state_cb(id, property, value, old_value, opaque):
    log.info(f"Set switch {id}, property {property} to {value}")
    tasmota.set_switch_state(sonoff_ids[id].sonoff_id, value)


def scheduler_start(db):
    scheduler = threading.Thread(target=scheduler_task, args=[db])
    scheduler.start()
    tasmota.start()
    # tasmota.subscribe_to_switches()
    from app.data.sonoff import DSonoff
    DSonoff.properties.subscribe_set("active", set_sonoff_state_cb, None)


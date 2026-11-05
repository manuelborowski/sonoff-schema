import datetime
from app.data.sonoff import Sonoff, dsonoff
from app.data.scheme import Scheme
from app import socketio, app
from app.data.mqtt import Tasmota
from eventlet import sleep


#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

sonoff_sonoff_ids = {}
sonoff_ids = {}
currrent_sonoffs = []


tasmota = Tasmota(app, log)
DAYS_OF_WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def time_in_minutes(value):
    try:
        hour, minute = map(int, (value or "").split(":"))
    except ValueError:
        return None
    if 0 <= hour < 24 and 0 <= minute < 60:
        return hour * 60 + minute
    return None


def active_scheme_ids(now):
    today = DAYS_OF_WEEK[now.weekday()]
    yesterday = DAYS_OF_WEEK[now.weekday() - 1]
    current_time = now.hour * 60 + now.minute
    schemes = Scheme.select().where(Scheme.active & (getattr(Scheme, today) | getattr(Scheme, yesterday)))
    scheme_on = set()
    for scheme in schemes:
        enabled_today = getattr(scheme, today)
        enabled_yesterday = getattr(scheme, yesterday)
        for on_value, off_value in ((scheme.on0, scheme.off0), (scheme.on1, scheme.off1)):
            on = time_in_minutes(on_value)
            off = time_in_minutes(off_value)
            if on is None or off is None:
                continue
            if on <= current_time < off and enabled_today:
                scheme_on.add(scheme.gid)
            elif on > off and ((enabled_today and current_time >= on) or (enabled_yesterday and current_time < off)):
                scheme_on.add(scheme.gid)
    return scheme_on


def scheduler_task(db):
    global sonoff_sonoff_ids
    global sonoff_ids
    with app.app_context():
        subscribed_sonoffs = []
        while True:
            try:
                temp_sonoffs = []
                enabled_sonoffs = Sonoff.select().where(Sonoff.sonoff_id != "") # enabled sonoffs only (sonoff_id is not empty)
                sonoff_sonoff_ids = {s.sonoff_id: s for s in enabled_sonoffs}
                sonoff_ids = {s.id: s for s in enabled_sonoffs}
                messages = tasmota.get_message_queue()
                for message in messages:
                    type, sonoff_id, data = message["type"], message["id"], message["data"]
                    sonoff = sonoff_sonoff_ids.get(sonoff_id)
                    if sonoff is None:
                        continue
                    if type == "state":
                        socketio.send({"id": f"sonoffstate-{sonoff.id}", "value": data}, json=True, namespace="/sonoffupdate")
                    elif type == "action":
                        dsonoff.properties.set(sonoff.id, "active", not sonoff.active)
                        sonoff.active = not sonoff.active
                    elif type == "ip":
                        socketio.send({"id": f"ip-{sonoff.id}", "value": data}, json=True, namespace="/sonoffupdate")
                for sonoff in enabled_sonoffs:
                    if sonoff.sonoff_id not in subscribed_sonoffs:
                        tasmota.subscribe_to_switch(sonoff.sonoff_id)
                        subscribed_sonoffs.append(sonoff.sonoff_id)
                    temp_sonoffs.append(sonoff.sonoff_id)
                not_valid_sonoffs = list(set(subscribed_sonoffs) ^ set(temp_sonoffs)) # list of disabled sonoffs, i.e. sonoff_id is empty
                subscribed_sonoffs = list(set(subscribed_sonoffs) ^ set(not_valid_sonoffs)) # update list of subscribed sonoffs
                for sonoff_id in not_valid_sonoffs:
                     tasmota.unsubscribe_from_switch(sonoff_id)
                for sonoff_id in subscribed_sonoffs:
                    tasmota.request_status(sonoff_id)

                scheme_on = active_scheme_ids(datetime.datetime.now())
                for sonoff in enabled_sonoffs:
                    if sonoff.mode != Sonoff.Mode.auto:
                        continue
                    schemes = sonoff.schemes if isinstance(sonoff.schemes, list) else []
                    active = any(gid in scheme_on for gid in schemes)
                    if sonoff.active != active:
                        dsonoff.properties.set(sonoff.id, "active", active)
            except Exception as e:
                log.error(f"task error, {e}")
            sleep(2)


def set_sonoff_state_cb(id, property, value, old_value, opaque):
    # log.info(f"Set switch {id}, property {property} to {value}")
    tasmota.set_switch_state(sonoff_ids[id].sonoff_id, value)


def scheduler_start(db):
    tasmota.start()
    dsonoff.properties.subscribe_set("active", set_sonoff_state_cb, None)
    socketio.start_background_task(target= lambda: scheduler_task(db))


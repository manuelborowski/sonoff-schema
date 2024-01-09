import datetime
from app.data.sonoff import Sonoff, dsonoff
from app.data.scheme import Scheme
from app import socketio, app
from flask_socketio import send
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


def scheduler_task(db):
    global sonoff_sonoff_ids
    global sonoff_ids
    days_of_week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    onoff_template = [["on0", True], ["off0", False], ["on1", True], ["off1", False]]
    with app.app_context():
        subscribed_sonoffs = []
        prev_active_schemes = {}
        while True:
            try:
                temp_sonoffs = []
                enabled_sonoffs = Sonoff.select().where(Sonoff.sonoff_id != "") # enabled sonoffs only (sonoff_id is not empty)
                sonoff_sonoff_ids = {s.sonoff_id: s for s in enabled_sonoffs}
                sonoff_ids = {s.id: s for s in enabled_sonoffs}
                messages = tasmota.get_message_queue()
                for message in messages:
                    type, sonoff_id, data = message["type"], message["id"], message["data"]
                    if type == "state":
                        send({"id": f"sonoffstate-{sonoff_sonoff_ids[sonoff_id].id}", "value": data}, json=True, broadcast=True, namespace=f"/sonoffupdate")
                    elif type == "action":
                        dsonoff.properties.set(sonoff_sonoff_ids[sonoff_id].id, "active", not sonoff_sonoff_ids[sonoff_id].active)
                    elif type == "ip":
                        send({"id": f"ip-{sonoff_sonoff_ids[sonoff_id].id}", "value": data}, json=True, broadcast=True, namespace=f"/sonoffupdate")
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

                # iterate over the schemes and compare the current day/time with the scheme days and times.  Select, per scheme, the day/time that is the closest, but smaller, than the current time.
                # Store in active_schemes the action, associated with the closest scheme-time
                now = datetime.datetime.now()
                reference_time = f"{int(now.hour):02d}:{int(now.minute):02d}"
                current_active_schemes = {} # list of valid schemes with, together with a state (i.e. associated sonoffs are off or on)
                applicable_schemes = Scheme.select().where(Scheme.active==True, getattr(Scheme, days_of_week[now.weekday()]) == True) # select applicable schemes (active and current day is enabled)
                for scheme in applicable_schemes:
                    for onoff in onoff_template:
                        property = getattr(scheme, onoff[0])
                        if property != "":
                            h, m = property.split(":")
                            property_time = f"{int(h):02d}:{int(m):02d}"
                            if property_time <= reference_time:
                                if scheme.gid not in current_active_schemes or property_time > current_active_schemes[scheme.gid]["time"]:
                                    current_active_schemes[scheme.gid] = {"time": property_time, "action": onoff[1]}
                    if scheme.gid not in current_active_schemes:
                        current_active_schemes[scheme.gid] = {"time": "00:00", "action": False}
                # consider transitions only, i.e. when action goes from True to False or vice verse.
                current_gids = set(current_active_schemes.keys())
                prev_gids = set(prev_active_schemes.keys())
                # present in current, not present in prev
                for gid in list((current_gids ^ prev_gids) & current_gids):
                    prev_active_schemes[gid] = current_active_schemes[gid]
                    del(current_active_schemes[gid])
                # present in prev, not present in current
                for gid in list((current_gids ^ prev_gids) & prev_gids):
                    del(prev_active_schemes[gid])
                # present in prev and current
                for gid in list(current_gids & prev_gids):
                    if prev_active_schemes[gid]["action"] == current_active_schemes[gid]["action"]:
                        del(current_active_schemes[gid])
                    else:
                        prev_active_schemes[gid] = current_active_schemes[gid]

                if current_active_schemes:
                    update_sonoffs = {} # a list of sonoffs (sonoff_id), together with an action (on or off)
                    for sonoff in enabled_sonoffs:
                        if sonoff.mode == Sonoff.Mode.auto:
                            for gid in sonoff.schemes:
                                if gid in current_active_schemes:
                                    update_sonoffs[sonoff.sonoff_id] = current_active_schemes[gid]["action"]
                    for sonoff_id, state in update_sonoffs.items():
                        dsonoff.properties.set(sonoff_sonoff_ids[sonoff_id].id, "active", state)
                sleep(2)
            except Exception as e:
                log.error(f"task error, {e}")


def set_sonoff_state_cb(id, property, value, old_value, opaque):
    # log.info(f"Set switch {id}, property {property} to {value}")
    tasmota.set_switch_state(sonoff_ids[id].sonoff_id, value)


def scheduler_start(db):
    tasmota.start()
    socketio.start_background_task(target= lambda: scheduler_task(db))
    from app.data.sonoff import DSonoff
    DSonoff.properties.subscribe_set("active", set_sonoff_state_cb, None)


from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app import LOG_FILENAME, log_handler, socketio, version, app
import datetime

#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

from app.application.sonoff import ASonoff
from app.application.scheme import AScheme
from app.data.logs import read_entries, read_switch_history

bp = Blueprint('index', __name__,)
index_url = f'/{app.config["INDEX_URL"]}'


@bp.route(index_url)
def hello():
    sonoffs = ASonoff.get_sonoffs()
    for sonoff in sonoffs:
        sonoff["ip"] = "xxx"
    return render_template("index.html", page="devices", rows=sonoffs, version=version)


@bp.route(f'{index_url.rstrip("/")}/schemes')
def schemes():
    return render_template("index.html", page="schemes", rows=AScheme.get_schemes(), version=version)


@bp.route(f'{index_url.rstrip("/")}/logging')
def logging_page():
    today = datetime.date.today()
    last_month = today.replace(day=1) - datetime.timedelta(days=1)
    default_start = last_month.replace(day=min(today.day, last_month.day))
    date_from = request.args.get("from", default_start.isoformat())
    date_until = request.args.get("until", today.isoformat())
    try:
        start = datetime.date.fromisoformat(date_from)
        end = datetime.date.fromisoformat(date_until)
        if start > end:
            raise ValueError
    except ValueError:
        return render_template("index.html", page="logging", version=version, date_from=date_from, date_until=date_until, date_error=True), 400

    entries = read_entries(LOG_FILENAME, log_handler.backupCount, start, end)
    return render_template("index.html", page="logging", version=version, date_from=start.isoformat(), date_until=end.isoformat(), entries=entries)


@bp.route(f'{index_url.rstrip("/")}/history')
def history():
    now = datetime.datetime.now()
    today = now.date()
    week = min(max(request.args.get("week", 0, type=int), 0), (today.toordinal() - 7) // 7)
    last_day = today - datetime.timedelta(weeks=week)
    first_day = last_day - datetime.timedelta(days=6)
    start = datetime.datetime.combine(first_day, datetime.time.min)
    end = start + datetime.timedelta(days=7)
    device_ids = (row["sonoff_id"] for row in ASonoff.get_sonoffs())
    timelines, has_older = read_switch_history(LOG_FILENAME, log_handler.backupCount, start, end, device_ids)
    duration = (end - start).total_seconds()
    history_data = {"start": first_day.isoformat(), "duration": duration, "knownUntil": min(duration, (now - start).total_seconds()), "devices": timelines}
    return render_template("index.html", page="history", version=version, first_day=first_day, last_day=last_day, week=week, has_older=has_older, history=history_data)


@bp.route(f'{index_url.rstrip("/")}/devices', methods=["POST", "DELETE"])
def manage_devices():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("sonoff_id"), str):
        return {"error": "Ongeldige apparaatgegevens."}, 400

    sonoff_id = data["sonoff_id"]
    if request.method == "POST":
        sonoff_id = sonoff_id.strip()
        if not sonoff_id or len(sonoff_id) > 255 or any(char in sonoff_id for char in "\x00/+#"):
            return {"error": "Geef een geldige Sonoff-id zonder /, + of #."}, 400
        if not ASonoff.add_device(sonoff_id):
            return {"error": "Deze Sonoff-id bestaat al."}, 409
        return "", 201

    device_id = data.get("id")
    if type(device_id) is not int or not 0 < device_id < 2**63:
        return {"error": "Ongeldig apparaat."}, 400
    if not ASonoff.delete_device(device_id, sonoff_id):
        return {"error": "Het apparaat is gewijzigd of al verwijderd. Vernieuw de pagina."}, 409
    return "", 204


@socketio.on('json', namespace="/sonoffupdate")
def handle_json(data):
    try:
        ASonoff.set_property(data["id"], data["value"])
    except Exception as e:
        log.error(f"handle_json, sonoffupdate error, {e}")


def broadcast_changed_property(id, property, value, old_value, opaque):
    socketio.send({"id": f"{property}-{id}", "value": value}, json=True, namespace=f"/{opaque}")


ASonoff.subscribe_set_property("*", broadcast_changed_property, "sonoffupdate")


@socketio.on('json', namespace="/schemeupdate")
def handle_json(data):
    try:
        AScheme.set_property(data["id"], data["value"])
    except Exception as e:
        log.error(f"handle_json, schemeupdate error, {e}")

AScheme.subscribe_set_property("*", broadcast_changed_property, "schemeupdate")

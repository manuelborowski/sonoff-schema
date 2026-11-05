from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app import socketio, version, app
from flask_socketio import send
import time, datetime

#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

from app.application.sonoff import ASonoff
from app.application.scheme import AScheme

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
    send({"id": f"{property}-{id}", "value": value}, json=True, broadcast=True, namespace=f"/{opaque}")


ASonoff.subscribe_set_property("*", broadcast_changed_property, "sonoffupdate")


@socketio.on('json', namespace="/schemeupdate")
def handle_json(data):
    try:
        AScheme.set_property(data["id"], data["value"])
    except Exception as e:
        log.error(f"handle_json, schemeupdate error, {e}")

AScheme.subscribe_set_property("*", broadcast_changed_property, "schemeupdate")

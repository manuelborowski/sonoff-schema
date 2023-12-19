from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app import socketio, version
from flask_socketio import send
import time, datetime

#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

from app.application.sonoff import ASonoff
from app.application.scheme import AScheme

bp = Blueprint('index', __name__,)


@bp.route('/')
def hello():
    sonoffs = ASonoff.get_sonoffs()
    for sonoff in sonoffs:
        sonoff["ip"] = "xxx"
    schemes = AScheme.get_schemes()
    return render_template("index.html", sonoffs=sonoffs, schemes=schemes, version=version)


@socketio.on('json', namespace="/sonoffupdate")
def handle_json(data):
    try:
        ASonoff.update_property(data["id"], data["value"])
    except Exception as e:
        log.error(f"handle_json, sonoffupdate error, {e}")


def broadcast_changed_property(id, property, value, old_value, opaque):
    send({"id": f"{property}-{id}", "value": value}, json=True, broadcast=True, namespace=f"/{opaque}")


ASonoff.subscribe_set_property("*", broadcast_changed_property, "sonoffupdate")


@socketio.on('json', namespace="/schemeupdate")
def handle_json(data):
    try:
        AScheme.update_property(data["id"], data["value"])
    except Exception as e:
        log.error(f"handle_json, schemeupdate error, {e}")

AScheme.subscribe_set_property("*", broadcast_changed_property, "schemeupdate")

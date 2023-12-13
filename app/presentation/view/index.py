from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app import socketio
from flask_socketio import send
import time, datetime

from app.application.sonoff import ASonoff
from app.application.scheme import AScheme

bp = Blueprint('index', __name__,)


@bp.route('/')
def hello():
    sonoffs = ASonoff.get_sonoffs()
    for sonoff in sonoffs:
        sonoff["ip"] = "xxx"
    schemes = AScheme.get_schemes()
    return render_template("index.html", sonoffs=sonoffs, schemes=schemes)


@socketio.on('json', namespace="/sonoffstate")
def handle_json(data):
    try:
        ASonoff.set_sonoff_property(data["id"], data["value"])
            # send({"id": data["id"], "value": data["value"]}, json=True, broadcast=True, namespace="/sonoffstate")
        # time.sleep(3)
        # send({"id": data["id"], "value": not data["value"]}, json=True, broadcast=True, namespace="/sonoffstate")
    except Exception as e:
        print(e)


def broadcast_changed_property(id, property, value, old_value, opaque):
    send({"id": f"{property}-{id}", "value": value}, json=True, broadcast=True, namespace=f"/{opaque}")


ASonoff.subscribe_set_property("*", broadcast_changed_property, "sonoffstate")


@socketio.on('json', namespace="/schemestate")
def handle_json(data):
    try:
        AScheme.set_property(data["id"], data["value"])
            # send({"id": data["id"], "value": data["value"]}, json=True, broadcast=True, namespace="/schemestate")
        # time.sleep(3)
        # send({"id": data["id"], "value": not data["value"]}, json=True, broadcast=True, namespace="/schemestate")
    except Exception as e:
        print(e)

AScheme.subscribe_set_property("*", broadcast_changed_property, "schemestate")

from peewee import CharField, BooleanField
from playhouse.sqlite_ext import JSONField
from .db import BaseModel, BaseProperties


class Sonoff(BaseModel):
    class State():
        on = "AAN"
        off = "UIT"
        auto = "AUTO"

    sonoff_id = CharField()
    location = CharField()
    mode = CharField(default=State.off)
    active = BooleanField(default=False)
    schemes = JSONField()


class DSonoff():
    properties = BaseProperties(Sonoff)

dsonoff = DSonoff()

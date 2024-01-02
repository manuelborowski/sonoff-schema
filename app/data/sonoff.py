from peewee import CharField, BooleanField
from playhouse.sqlite_ext import JSONField
from .db import BaseModel, BaseProperties


class Sonoff(BaseModel):
    class Mode():
        auto = "AUTO"
        man = "MAN"

    sonoff_id = CharField(default="")
    location = CharField(default="")
    mode = CharField(default=Mode.man)
    active = BooleanField(default=False)
    schemes = JSONField()

    @classmethod
    def get_next_mode(cls, current_mode):
        next_mode = Sonoff.Mode.man if current_mode == Sonoff.Mode.auto else Sonoff.Mode.auto
        return next_mode



class DSonoff():
    properties = BaseProperties(Sonoff)

dsonoff = DSonoff()

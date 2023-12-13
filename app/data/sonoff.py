from peewee import CharField, BooleanField
from playhouse.sqlite_ext import JSONField
from .db import BaseModel, BaseProperties

class Sonoff(BaseModel):
    sonoff_id = CharField()
    location = CharField()
    active = BooleanField(default=True)
    schemes = JSONField()

class DSonoff():
    properties = BaseProperties(Sonoff)

dsonoff = DSonoff()

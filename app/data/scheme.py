from peewee import CharField, BooleanField, IntegerField
from .db import BaseModel, BaseProperties

class Scheme(BaseModel):
    gid = IntegerField(default=0)
    active = BooleanField(default=True)
    mon = BooleanField(default=0)
    tue = BooleanField(default=0)
    wed = BooleanField(default=0)
    thu = BooleanField(default=0)
    fri = BooleanField(default=0)
    sat = BooleanField(default=0)
    sun = BooleanField(default=0)
    on0 = CharField(default="")
    off0 = CharField(default="")
    on1 = CharField(default="")
    off1 = CharField(default="")


class DScheme():
    properties = BaseProperties(Scheme)

dscheme = DScheme()



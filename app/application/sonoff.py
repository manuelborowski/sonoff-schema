from app.data.sonoff import Sonoff, dsonoff

class ASonoff():
    @classmethod
    def get_sonoffs(cls):
        return [ r for r in Sonoff.select().dicts()]

    @classmethod
    def set_sonoff_property(cls, id_code, value):
        property, id = id_code.split("-")
        return dsonoff.properties.set_property(id, property, value)

    @classmethod
    def subscribe_set_property(cls, property, cb, opaque):
        return dsonoff.properties.subscribe_set_property(property, cb, opaque)
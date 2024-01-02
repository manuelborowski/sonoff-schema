from app.data.sonoff import Sonoff, dsonoff

class ASonoff():
    @classmethod
    def get_sonoffs(cls):
        return [ r for r in Sonoff.select().dicts()]

    # depending on the property and current value, calculate the new value
    @classmethod
    def set_property(cls, id_code, value):
        property, id = id_code.split("-")
        if property == "mode":
            value = Sonoff.get_next_mode(value)
        if property == "active":
            value = not value
        # if property == "mode":
        #     next_states = {"UIT": "AAN", "AAN": "AUTO", "AUTO": "UIT"}
        #     value = next_states[value]
        #     if value != "AUTO":
        #         dsonoff.properties.set(id, "active", value == "AAN")
        return dsonoff.properties.set(id, property, value)

    @classmethod
    def subscribe_set_property(cls, property, cb, opaque):
        return dsonoff.properties.subscribe_set(property, cb, opaque)
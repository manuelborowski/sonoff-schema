from app.data.scheme import Scheme, dscheme

class AScheme():
    @classmethod
    def get_schemes(cls):
        schemes = [s for s in Scheme.select().order_by(Scheme.gid, Scheme.id).dicts()]
        return schemes

    @classmethod
    def set_property(cls, id_code, value):
        property, id = id_code.split("-")
        return dscheme.properties.set(id, property, value)

    @classmethod
    def update_property(cls, id_code, value):
        property, id = id_code.split("-")
        if property in ["active", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            value = not value
        return dscheme.properties.set(id, property, value)

    @classmethod
    def subscribe_set_property(cls, property, cb, opaque):
        return dscheme.properties.subscribe_set(property, cb, opaque)
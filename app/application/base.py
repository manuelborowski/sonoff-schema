class DataBase():
    @classmethod
    def set_property(cls, id_code, value):
        property, id = id_code.split("-")
        return cls.set_property(id, property, value)

    @classmethod
    def subscribe_set_property(cls, property, cb, opaque):
        return cls.subscribe_set_property(property, cb, opaque)
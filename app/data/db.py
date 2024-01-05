from peewee import Model
from playhouse.shortcuts import ThreadSafeDatabaseMetadata
from app import dbase, app

#logging on file level
import logging
from app import top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")

@app.before_request
def before_request():
    dbase.connect(reuse_if_open=True)

@app.after_request
def after_request(response):
    dbase.close()
    return response



class BaseModel(Model):
    class Meta:
        database = dbase
        model_metadata_class = ThreadSafeDatabaseMetadata


class BaseProperties():
    def __init__(self, model):
        self.model = model
        self.subscribed_properties = {}

    def set(self, id, property, value):
        id = int(id)
        item = self.model.select().where(self.model.id == id).get()
        old_value = getattr(item, property)
        setattr(item, property, value)
        item.save()
        for p in [property, "*"]:
            if p in self.subscribed_properties:
                for item in self.subscribed_properties[p]:
                    item[0](id, property, value, old_value, item[1])
        return True

    # if property is "*" => all properties
    def subscribe_set(self, property, cb, opaque):
        if property in self.subscribed_properties:
            self.subscribed_properties[property].append((cb, opaque))
        else:
            self.subscribed_properties[property] = [(cb, opaque)]

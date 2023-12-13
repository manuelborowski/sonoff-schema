from peewee import Model
from app import dbase, app
# import sqlite3
#
# import click


@app.before_request
def before_request():
    dbase.connect()

@app.after_request
def after_request(response):
    dbase.close()
    return response



class BaseModel(Model):
    class Meta:
        database = dbase


class BaseProperties():
    def __init__(self, model):
        self.model = model
        self.subscribed_properties = {}

    def set_property(self, id, property, value):
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
    def subscribe_set_property(self, property, cb, opaque):
        if property in self.subscribed_properties:
            self.subscribed_properties[property].append((cb, opaque))
        else:
            self.subscribed_properties[property] = [(cb, opaque)]
#
#
# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
#         g.db.row_factory = sqlite3.Row
#     return g.db
#
#
# def close_db(e=None):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()
#
#
# def init_db():
#     db = get_db()
#     with current_app.open_resource('schema.sql') as f:
#         db.executescript(f.read().decode('utf8'))
#
#
# @click.command('init-db')
# def init_db_command():
#     """Clear the existing data and create new tables."""
#     init_db()
#     click.echo('Initialized the database.')
#
#
# def init_app(app):
#     app.teardown_appcontext(close_db)
#     app.cli.add_command(init_db_command)
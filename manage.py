import os

from flask import Flask
from flask_script import Manager
from flask_script import Server
from flask_script import Shell
from flask_migrate import Migrate, MigrateCommand

from server.app import create_injector, create_app, create_event_mgr
from celery_source import provide_celery
from server.app.common import models
from server.app.injector_keys import Config, SQLAlchemy, MongoDB

app = create_app()
injector = create_injector(app)
config = injector.get(Config)
db = injector.get(SQLAlchemy)
mongo = injector.get(MongoDB)
manager = Manager(app)
celery = provide_celery(app)
migrate = Migrate(app, db)
event_mgr = create_event_mgr(app)


def make_shell_context():
    return {
        'app': app,
        'config': app.config,
        'db': db,
        'mongo': mongo,
        'injector': injector,
        'models': models,
        'celery': celery,
        'event_mgr': event_mgr
    }


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))


@manager.command
def init_db():
    from server.app.common.models import KeyValue, User

    KeyValue.insert_keyvalues()

    User.insert_users()


if __name__ == '__main__':
    manager.run()

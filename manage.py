from flask import Flask
from flask_script import Manager
from flask_script import Server
from flask_script import Shell
from injector import inject

from server.app import create_injector
from server.app.common import models
from server.app.injector_keys import Config, SQLAlchemy

injector = create_injector()
app = injector.get(Flask)
config = injector.get(Config)
db = injector.get(SQLAlchemy)
manager = Manager(app)


def make_shell_context():
    return {
        'app': app,
        'config': app.config,
        'db': db,
        'injector': injector,
        'models': models
    }

manager.add_command('shell', Shell(make_context=make_shell_context))
# *** put db migrate command here
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))

@manager.command
def init_db():
    from server.app.common.models import KeyValue

    KeyValue.insert_keyvalues()

if __name__ == '__main__':
    manager.run()

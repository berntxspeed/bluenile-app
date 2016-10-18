from flask import Flask
from flask_script import Manager
from flask_script import Server
from flask_script import Shell
from migrate.versioning import api
from injector import inject

from server.app import create_injector
from server.app.common import models
from server.app.injector_keys import Config, SQLAlchemy, MongoDB

import os.path
import imp

injector = create_injector()
app = injector.get(Flask)
config = injector.get(Config)
db = injector.get(SQLAlchemy)
mongo = injector.get(MongoDB)
manager = Manager(app)

SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_MIGRATE_REPO = config.get('SQLALCHEMY_MIGRATE_REPO')

def make_shell_context():
    return {
        'app': app,
        'config': app.config,
        'db': db,
        'mongo': mongo,
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

@manager.command
def db_create():
    db.create_all()
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

@manager.command
def db_downgrade():
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    api.downgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, v - 1)
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    print('Current database version: ' + str(v))

@manager.command
def db_migrate():
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % (v+1))
    tmp_module = imp.new_module('old_model')
    old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    exec(old_model, tmp_module.__dict__)
    script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, tmp_module.meta, db.metadata)
    open(migration, 'wt').write(script)
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    print('New migration saved as ' + migration)
    print('Current database version: ' + str(v))

@manager.command
def db_upgrade():
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    print('Current database version: ' + str(v))


if __name__ == '__main__':
    manager.run()

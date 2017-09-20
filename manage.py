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
# event_mgr = create_event_mgr(app)


def make_shell_context():
    return {
        'app': app,
        'config': app.config,
        'db': db,
        'mongo': mongo,
        'injector': injector,
        'models': models,
        'celery': celery,
        # 'event_mgr': event_mgr
    }


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0', port=5000,
                                        extra_files=['server/asset-config.yaml'],))


@manager.command
def init_db():
    from server.app.common.models.system_models import system_db
    from server.app.task_admin.services.account_creation_service import AccountCreationService

    # creates the system database
    account_service = AccountCreationService('test-account2', 'vitalik301@gmail.com', config)
    account_service.create_postgres('bluenile', system_db)
    account_service.execute()


@manager.command
def reset_alembic_version():
    from sqlalchemy import create_engine

    # get db uris for all accounts
    account_dbs = []
    from server.app.common.models.system_models import ClientAccount, session_scope
    with session_scope() as session:
        client_accounts_result = session.query(ClientAccount).all()
        for an_account in client_accounts_result:
            account_dbs.append(an_account.database_uri)

    # alembic_version tables in each catalog
    for an_account_db in account_dbs:
        try:
            engine = create_engine(an_account_db)
            engine.execute("delete from alembic_version")
            print(f'SUCCESS: Cleared alembic_version table for {an_account_db}')
        except Exception:
            print(f'FAILURE: Could not clear alembic_version table for {an_account_db}')
            print()

if __name__ == '__main__':
    manager.run()

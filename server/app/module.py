from flask import Flask
from flask_cache import Cache
from injector import Module
from injector import singleton
from injector import inject
from injector import provides

from .injector_keys import Config, SimpleCache, Logging, SQLAlchemy, MongoDB, UserSessionConfig, DBSession

import logging
import sys


class AppModule(Module):
    @singleton
    @inject(app=Flask)
    @provides(Config)
    def provide_app_config(self, app):
        return app.config

    @singleton
    @provides(SQLAlchemy)
    def provides_sqlalchemy(self):
        from .common.models.user_models import user_db
        return user_db

    @inject(app=Flask)
    @provides(UserSessionConfig)
    def provides_user_session_config(self, app):
        from flask import session
        return session.get('user_params')

    @inject(app=Flask, config=UserSessionConfig)
    @provides(DBSession)
    def provides_sqlalchemy_session(self, app, config):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(config.get('postgres_uri'))
        session = scoped_session(sessionmaker(bind=engine))

        return session

    @singleton
    @inject(app=Flask)
    @provides(MongoDB)
    def provides_mongodb(self, app):
        from .common.storage import provide_mongo
        return provide_mongo()

    @singleton
    @inject(app=Flask)
    @provides(SimpleCache)
    def provides_simple_cache(self, app):
        return Cache(app, config={'CACHE_TYPE': 'simple'})

    @singleton
    @inject(config=Config)
    @provides(Logging)
    def provides_logging(self, config):
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        logger = logging.getLogger(config['LOGGER_NAME'])
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.ERROR)
        logger.addHandler(stream_handler)
        return logger


def get_modules():
    # import other modules
    from .auth.module import AuthModule
    from .stats.module import StatsModule
    from .data.module import UserDataModule
    from .data_builder.module import SqlQueryModule
    from .emails.module import EmailModule

    return [
        AppModule(),
        AuthModule(),
        StatsModule(),
        UserDataModule(),
        SqlQueryModule(),
        EmailModule()
    ]


def get_blueprints():
    # import all blueprints
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .stats import stats as stats_blueprint
    from .data import data as data_blueprint
    from .data_builder import databuilder as data_builder_blueprint
    from .task_admin import taskadmin as task_admin_blueprint
    from .emails import emails as emails_blueprint
    return [
        main_blueprint,
        auth_blueprint,
        stats_blueprint,
        data_blueprint,
        data_builder_blueprint,
        task_admin_blueprint,
        emails_blueprint
    ]

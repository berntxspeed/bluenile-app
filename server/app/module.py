from flask import Flask
from flask_cache import Cache
from injector import Module
from injector import singleton
from injector import inject
from injector import provides

from .injector_keys import Config, SimpleCache, Logging, SQLAlchemy, MongoDB, Celery

# import other modules
from .auth.module import AuthModule
from .stats.module import StatsModule
from .data.module import DataModule

# import all blueprints
from .main import main as main_blueprint
from .auth import auth as auth_blueprint
from .stats import stats as stats_blueprint
from .data import data as data_blueprint

import logging
import sys

class AppModule(Module):

    @singleton
    @inject(app=Flask)
    @provides(Config)
    def provide_app_config(self, app):
        return app.config

    @inject(app=Flask)
    @provides(SQLAlchemy)
    def provides_sqlalchemy(self, app):
        from .common.models import db
        return db

    @singleton
    @inject(app=Flask)
    @provides(MongoDB)
    def provides_mongodb(self, app):
        from .common.storage import provide_mongo
        return provide_mongo()

    @singleton
    @inject(app=Flask)
    @provides(Celery)
    def provides_celery(self, app):
        from .common.storage import provide_celery
        return provide_celery(app)

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


modules = [
    AppModule(),
    AuthModule(),
    StatsModule(),
    DataModule()
]

blueprints = [
    main_blueprint,
    auth_blueprint,
    stats_blueprint,
    data_blueprint
]

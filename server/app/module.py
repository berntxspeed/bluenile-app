from flask import Flask
from flask_cache import Cache
from injector import Module
from injector import singleton
from injector import inject
from injector import provides

from .injector_keys import Config, SimpleCache, Logging, SQLAlchemy

# import other modules

# import all blueprints
from .main import main as main_blueprint

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
    AppModule()
]

blueprints = [
    main_blueprint
]

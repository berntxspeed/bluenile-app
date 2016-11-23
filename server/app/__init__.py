from flask import Flask
from flask_injector import FlaskInjector
from flask_login import LoginManager
import flask_restless as Restless
from flask_assets import Environment
from werkzeug import SharedDataMiddleware
from webassets.filter import register_filter
from celery import Celery

from server.app.injector_keys import MongoDB
from .module import blueprints
from .module import modules
from ..config import config

import sys
import os


def get_config():
    env = os.getenv('APP_SETTINGS')
    config_obj = config.get(env)
    if not config_obj:
        sys.exit('Incorrect ENV: %s' % env)
    return config_obj


def create_app():
    config_obj = get_config()

    app = Flask(__name__,
                static_folder=config_obj.STATIC_FOLDER,
                template_folder=config_obj.TEMPLATE_FOLDER,
                static_url_path=config_obj.STATIC_URL_PATH)

    app.debug = True
    app.config.from_object(config_obj)
    config_obj.init_app(app)

    # Enables static file serving on heroku
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {'/': config_obj.STATIC_FOLDER})

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    return app


def provide_celery(app):
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], include='server.app.common.workers.module')
    celery.conf.update(app.config)

    return celery


def create_injector(app=None):
    if app is None:
        app = create_app()

    injector = FlaskInjector(app=app, modules=modules).injector
    init_db(app)
    init_mongo(app, injector.get(MongoDB))
    init_login_manager(app)
    init_assets(app)
    return injector


def init_db(app):
    from .common.models import db, SendJob, EmlSend, EmlOpen, EmlClick, Customer, Artist
    db.init_app(app)

    # create the Flask-Restless API manager
    manager = Restless.APIManager(app, flask_sqlalchemy_db=db)

    # create the api endpoints, which will be available by /api/<tblname>
    manager.create_api(SendJob, methods=['GET'])
    manager.create_api(EmlSend, methods=['GET'])
    manager.create_api(EmlOpen, methods=['GET'])
    manager.create_api(EmlClick, methods=['GET'])
    manager.create_api(Artist, methods=['GET'])
    manager.create_api(Customer, methods=['GET'])


def init_mongo(app, mongo):
    mongo.init_app(app)


def init_login_manager(app):
    from .common.models import User
    login_manager = LoginManager()
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.init_app(app)


def init_assets(app):
    from .common.utils.assets import bundles
    from dukpy.webassets import BabelJS

    register_filter(BabelJS)

    assets = Environment(app)
    assets.from_yaml(get_config().ASSET_CONFIG_FILE)

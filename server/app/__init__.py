from flask import Flask
from flask_injector import FlaskInjector
from werkzeug import SharedDataMiddleware

from .module import blueprints
from .module import modules
from ..config import config

import sys


def create_app():
    env = 'local'
    config_obj = config.get(env)
    if not config_obj:
        sys.exit('Incorrect ENV: %s' % env)

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

def create_injector(app=None):
    if app is None:
        app = create_app()
    injector = FlaskInjector(app=app, modules=modules).injector
    init_db(app)
    return injector

def init_db(app):
    from .common.models import db
    db.init_app(app)

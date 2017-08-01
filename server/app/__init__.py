import os

import sys
from flask import Flask
from flask_session import Session
from flask_injector import FlaskInjector
from flask_login import LoginManager
import flask_restless as Restless
from flask_assets import Environment
from werkzeug import SharedDataMiddleware
from webassets.filter import register_filter

from server.app.injector_keys import MongoDB
from ..config import config


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
    Session(app)

    return app


def configure(app):
    from .module import get_blueprints

    # Enables static file serving on heroku
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {'/': app.config.get('STATIC_FOLDER')})

    for blueprint in get_blueprints():
        app.register_blueprint(blueprint)

    create_app()


def create_injector(app=None):
    from .module import get_modules

    configure(app)

    injector = FlaskInjector(app=app, modules=get_modules()).injector
    init_db(app)
    init_mongo(app, injector.get(MongoDB))
    init_login_manager(app)
    init_assets(app)
    return injector


def init_db(app):
    from .common.models.system_models import system_db
    system_db.init_app(app)

    # TODO:remove this
    # from .common.models.user_models import user_db
    # user_db.init_app(app)


def init_mongo(app, mongo):
    mongo.init_app(app)


def init_login_manager(app):
    from server.app.auth.services import OktaUser, OktaUsersClient
    login_manager = LoginManager()
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        users_client = OktaUsersClient('https://dev-198609.oktapreview.com',
                                       '00lKRIDx7J6jlox9LwftcKfqKqkoRSKwY5dhslMs9z')
        okta_user = users_client.get_user(user_id)
        return OktaUser(okta_user)

    login_manager.init_app(app)


def init_assets(app):
    from dukpy.webassets import BabelJS

    register_filter(BabelJS)

    assets = Environment(app)
    assets.from_yaml(get_config().ASSET_CONFIG_FILE)


def create_event_mgr(app):
    from .common.utils.event_mgr import EventMgr
    from .common.models.user_models import user_db, Event, EventDefinition
    from flask_sqlalchemy import SignallingSession


    event_mgr = EventMgr(db, Event, EventDefinition)

    # process record updates
    @user_db.event.listens_for(SignallingSession, 'before_flush')
    def on_flush(session, flush_context, instances):
        event_mgr.log_update_events(session)

    # process record inserts
    @user_db.event.listens_for(SignallingSession, 'after_flush')
    def after_flush(session, flush_context):
        event_mgr.log_insert_events(session)

    # update event defs loaded in event_mgr
    @user_db.event.listens_for(EventDefinition, 'after_insert', retval=True)
    def on_update(mapper, connection, target):
        event_mgr.refresh_event_defs()
        return target

    # update event defs loaded in event_mgr
    @user_db.event.listens_for(EventDefinition, 'after_update', retval=True)
    def on_update(mapper, connection, target):
        event_mgr.refresh_event_defs()
        return target

    return event_mgr

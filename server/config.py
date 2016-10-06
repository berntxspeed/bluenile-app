import os

LOCAL = 'local'
TEST = 'test'
STG = 'stg'
PROD = 'prod'

class Config(object):
    # Application
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    STATIC_FOLDER = os.path.join(PROJECT_ROOT, '..', 'static')
    TEMPLATE_FOLDER = os.path.join(PROJECT_ROOT, 'app', 'common', 'templates')
    STATIC_URL_PATH = '/static'
    LOGGER_NAME = 'simple_di_flask_app'
    PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Cache
    CACHE_TYPE = 'simple'

    @classmethod
    def init_app(cls, app):
        pass


class LocalConfig(Config):
    ENV = LOCAL

    # Application
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(PROJECT_ROOT, '..', 'tmp', 'app.db')
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

    @classmethod
    def init_app(cls, app):
        super(LocalConfig, cls).init_app(app)
        if app.debug:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)


class TestConfig(Config):
    ENV = TEST


class StgConfig(Config):
    ENV = STG


class ProdConfig(Config):
    ENV = PROD

    # Application
    STATIC_FOLDER = os.path.join(Config.PROJECT_ROOT, 'public')
    STATIC_URL_PATH = '/public'


config = {
    LOCAL: LocalConfig,
    TEST: TestConfig,
    STG: StgConfig,
    PROD: ProdConfig
}

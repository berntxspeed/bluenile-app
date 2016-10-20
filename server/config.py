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
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(PROJECT_ROOT, '..', 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MONGO_URI = os.getenv('MONGODB_URI')

    # Cache
    CACHE_TYPE = 'simple'

    # Oauth2 Credentials
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    TWITTER_APP_ID = os.getenv('TWITTER_APP_ID')
    TWITTER_APP_SECRET = os.getenv('TWITTER_APP_SECRET')

    # External Data Sources
    CUSTOMER_DATA_SOURCE = os.getenv('CUSTOMER_DATA_SOURCE')
    ARTIST_DATA_SOURCE = os.getenv('ARTIST_DATA_SOURCE')
    EXT_DATA_CREDS = {
        'shopify': {
            'endpoint': os.getenv('SHOPIFY_API_ENDPOINT'),
            'id': os.getenv('SHOPIFY_API_APP_ID'),
            'secret': os.getenv('SHOPIFY_API_APP_SECRET')
        },
        'spotify': {
            'endpoint': os.getenv('SPOTIFY_API_ENDPOINT')
        }
    }
    @classmethod
    def init_app(cls, app):
        pass


class LocalConfig(Config):
    ENV = LOCAL

    # Application
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

    # Oauth2 Credentials
    FACEBOOK_APP_ID = '1414432525530848'
    FACEBOOK_APP_SECRET = '82a49f002a8bf1bdcf34a5adfa083914'
    TWITTER_APP_ID = 'MzZ2zXpjQxGSl6gAm6VwQrIv4'
    TWITTER_APP_SECRET = 'adfuzYNtIoAkoBHKTnQGxGtyYBHbihgyf2qG3pr3o6QaqcWMyv'
    # ***add google login

    # assets configuration (js/css files)
    ASSETS_DEBUG = True # forces flask to not merge asset files into one file

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

    @classmethod
    def init_app(cls, app):
        super(StgConfig, cls).init_app(app)
        if app.debug:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)


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

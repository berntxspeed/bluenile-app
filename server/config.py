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
    EMAIL_DATA_SOURCE = os.getenv('EMAIL_DATA_SOURCE')

    EXT_DATA_CREDS = {
        'shopify': {
            'endpoint': os.getenv('SHOPIFY_API_ENDPOINT'),
            'id': os.getenv('SHOPIFY_API_APP_ID'),
            'secret': os.getenv('SHOPIFY_API_APP_SECRET')
        },
        'spotify': {
            'endpoint': os.getenv('SPOTIFY_API_ENDPOINT')
        },
        'marketing_cloud': {
            'ftp_url': os.getenv('MARKETING_CLOUD_FTP_URL'),
            'ftp_user': os.getenv('MARKETING_CLOUD_FTP_USER'),
            'ftp_pass': os.getenv('MARKETING_CLOUD_FTP_PASS'),
            'filename': os.getenv('MARKETING_CLOUD_FTP_FILENAME'),
            'filepath': os.getenv('MARKETING_CLOUD_FTP_FILEPATH')
        }
    }

    @classmethod
    def init_app(cls, app):
        pass


class LocalConfig(Config):
    ENV = LOCAL

    # Application
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

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

    # Application
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

    # assets configuration (js/css files)
    ASSETS_DEBUG = True  # forces flask to not merge asset files into one file

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

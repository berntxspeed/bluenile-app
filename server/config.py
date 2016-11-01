import os

LOCAL = 'local'
TEST = 'test'
DEV = 'dev'
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
    SEND_FILE_MAX_AGE_DEFAULT = 31536000

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
    GOOGLE_APP_ID = os.getenv('GOOGLE_APP_ID')
    GOOGLE_APP_SECRET = os.getenv('GOOGLE_APP_SECRET')

    # External Data Sources
    CUSTOMER_DATA_SOURCE = os.getenv('CUSTOMER_DATA_SOURCE')
    ARTIST_DATA_SOURCE = os.getenv('ARTIST_DATA_SOURCE')
    EMAIL_DATA_SOURCE = os.getenv('EMAIL_DATA_SOURCE')
    EMAIL_DATA_DEST = os.getenv('EMAIL_DATA_DEST')

    EXT_DATA_CREDS = {
        'shopify': {
            'endpoint': os.getenv('SHOPIFY_API_ENDPOINT'),
            'id': os.getenv('SHOPIFY_API_APP_ID'),
            'secret': os.getenv('SHOPIFY_API_APP_SECRET')
        },
        'spotify': {
            'endpoint': os.getenv('SPOTIFY_API_ENDPOINT')
        },
        'marketingcloud_ftp': {
            'ftp_url': os.getenv('MARKETING_CLOUD_FTP_URL'),
            'ftp_user': os.getenv('MARKETING_CLOUD_FTP_USER'),
            'ftp_pass': os.getenv('MARKETING_CLOUD_FTP_PASS'),
            'filename': os.getenv('MARKETING_CLOUD_FTP_FILENAME'),
            'filepath': os.getenv('MARKETING_CLOUD_FTP_FILEPATH')
        },
        'marketingcloud_api': {
            'id': os.getenv('FUELSDK_CLIENT_ID'),
            'secret': os.getenv('FUELSDK_CLIENT_SECRET'),
            'app_sig': os.getenv('FUELSDK_APP_SIGNATURE'),
            'wsdl': os.getenv('FUELSDK_DEFAULT_WSDL'),
            'auth_url': os.getenv('FUELSDK_AUTH_URL')
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

class DevConfig(Config):
    ENV = DEV

    # Application
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

    # Assets configuration (js/css files)
    ASSETS_DEBUG = True # Forces flask-assets to not merge/compress js files

    @classmethod
    def init_app(cls, app):
        super(DevConfig, cls).init_app(app)
        if app.debug:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)

class StgConfig(Config):
    ENV = STG

    # Application
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

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
    DEV: DevConfig,
    STG: StgConfig,
    PROD: ProdConfig
}

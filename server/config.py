import os
import redis

LOCAL = 'local'
TEST = 'test'
DEV = 'dev'
STG = 'stg'
PROD = 'prod'


class Config(object):
    # Application
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    STATIC_FOLDER = os.path.join(PROJECT_ROOT, '..', 'static')
    API_CONFIG_FILE = os.path.join(PROJECT_ROOT, '..', 'config', 'api_config.yml')
    TEMPLATE_FOLDER = os.path.join(PROJECT_ROOT, 'app', 'common', 'templates')
    STATIC_URL_PATH = '/static'
    LOGGER_NAME = 'simple_di_flask_app'
    PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SEND_FILE_MAX_AGE_DEFAULT = 31536000
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, '..', 'static/uploads')
    REDIS_URI = os.getenv('REDIS_URL')

    # Used by Flask-Session
    SESSION_TYPE = 'redis'

    # Database
    # SQLALCHEMY_BINDS = {
    #     'user_data':    'postgresql://localhost/simple_di_flask_dev',
    #     'appmeta':      'postgresql://localhost/bluenile',
    # }

    SQLALCHEMY_MIGRATE_REPO = os.path.join(PROJECT_ROOT, '..', 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MONGO_URI = os.getenv('MONGODB_URI')
    ASSET_CONFIG_FILE = os.path.join(PROJECT_ROOT, 'asset-config.yaml')

    REDIS_URI = os.getenv('REDIS_URL')
    CELERY_BROKER_URL = REDIS_URI

    # Used by Flask-Session
    SESSION_REDIS = redis.from_url(REDIS_URI)
    SYSTEM_DB_URI = os.getenv('SYSTEM_DB_URI')
    AWS_DB_URI_PREFIX = os.getenv('AWS_DB_URI_PREFIX')

    # Cache
    CACHE_TYPE = 'simple'

    # Oauth2 Credentials
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    GOOGLE_APP_ID = os.getenv('GOOGLE_APP_ID')
    GOOGLE_APP_SECRET = os.getenv('GOOGLE_APP_SECRET')

    # External Data Sources
    EMAIL_DATA_SOURCE = os.getenv('EMAIL_DATA_SOURCE')
    EMAIL_DATA_DEST = os.getenv('EMAIL_DATA_DEST')

    # Okta Authentication
    OKTA_URL = 'https://dev-198609.oktapreview.com'
    OKTA_API_KEY = '00lKRIDx7J6jlox9LwftcKfqKqkoRSKwY5dhslMs9z'

    EXT_DATA_CREDS = {
        'marketingcloud_api': {
            'id': os.getenv('FUELSDK_CLIENT_ID'),
            'secret': os.getenv('FUELSDK_CLIENT_SECRET'),
            'app_sig': os.getenv('FUELSDK_APP_SIGNATURE'),
            'wsdl': os.getenv('FUELSDK_DEFAULT_WSDL'),
            'auth_url': os.getenv('FUELSDK_AUTH_URL'),
            # for later 'endpoint': os.getenv('FUELSDK_RAW_ENDPOINT')
        # },
        # 'lead-perfection': {
        #     'ftp_url': os.getenv('MARKETING_CLOUD_FTP_URL'),
        #     'ftp_user': os.getenv('MARKETING_CLOUD_FTP_USER'),
        #     'ftp_pass': os.getenv('MARKETING_CLOUD_FTP_PASS'),
        #     'filename': os.getenv('LEAD_PERFECTION_FILENAME'),
        #     'filepath': os.getenv('LEAD_PERFECTION_FILEPATH')
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
    ASSETS_DEBUG = True  # Forces flask-assets to not merge/compress js files

    @classmethod
    def init_app(cls, app):
        super(DevConfig, cls).init_app(app)

        #if app.debug:
            #from flask_debugtoolbar import DebugToolbarExtension
            #DebugToolbarExtension(app)


class StgConfig(Config):
    ENV = STG

    # Application
    SECRET_KEY = 'Wju4$47388fjdfierhiue0945374539'

    @classmethod
    def init_app(cls, app):
        super(StgConfig, cls).init_app(app)
        #if app.debug:
            #from flask_debugtoolbar import DebugToolbarExtension
            #DebugToolbarExtension(app)


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

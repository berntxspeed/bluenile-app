from flask import session
from flask_oauthlib.client import OAuth
from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import FacebookAuth, GoogleAuth, OAuthBase, AuthServ
from ..injector_keys import Config, Logging, SQLAlchemy
from .services import AuthService


class AuthModule(Module):

    @singleton
    @provides(OAuthBase)
    def provides_oauthbase(self):
        return OAuth()

    @singleton
    @inject(oauth=OAuthBase, config=Config)
    @provides(FacebookAuth)
    def provide_facebook_auth(self, oauth, config):
        return oauth.remote_app('facebook',
                                base_url='https://graph.facebook.com',
                                request_token_url=None,
                                access_token_url='/oauth/access_token',
                                authorize_url='https://www.facebook.com/v2.8/dialog/oauth',
                                consumer_key=config['FACEBOOK_APP_ID'],
                                consumer_secret=config['FACEBOOK_APP_SECRET'],
                                request_token_params={'scope': 'email'}
                                )

    @singleton
    @inject(oauth=OAuthBase, config=Config)
    @provides(GoogleAuth)
    def provide_google_auth(self, oauth, config):
        return oauth.remote_app('google',
                                base_url='https://www.google.com/accounts/',
                                authorize_url='https://accounts.google.com/o/oauth2/auth',
                                request_token_url=None,
                                request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email'},
                                access_token_url='https://accounts.google.com/o/oauth2/token',
                                access_token_method='POST',
                                consumer_key=config['GOOGLE_APP_ID'],
                                consumer_secret=config['GOOGLE_APP_SECRET']
                                )

    @singleton
    @inject(config=Config,
            db=SQLAlchemy,
            logger=Logging,
            facebook_auth=FacebookAuth,
            google_auth=GoogleAuth)
    @provides(AuthServ)
    def provide_auth_service(
        self,
        config,
        db,
        logger,
        facebook_auth,
        google_auth):
        return AuthService(
            config=config,
            db=db,
            logger=logger,
            facebook_auth=facebook_auth,
            google_auth=google_auth,
            session=session)

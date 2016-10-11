from flask import session
from flask_oauthlib.client import OAuth
from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import FacebookAuth, TwitterAuth, OAuthBase, AuthServ
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
    @provides(TwitterAuth)
    def provide_twitter_auth(self, oauth, config):
        return oauth.remote_app('twitter',
                                base_url='https://api.twitter.com/1/',
                                request_token_url='https://api.twitter.com/oauth/request_token',
                                access_token_url='https://api.twitter.com/oauth/access_token',
                                authorize_url='https://api.twitter.com/oauth/authenticate',
                                consumer_key=config['TWITTER_APP_ID'],
                                consumer_secret=config['TWITTER_APP_SECRET']
                                )

    @singleton
    @inject(config=Config,
            db=SQLAlchemy,
            logger=Logging,
            facebook_auth=FacebookAuth,
            twitter_auth=TwitterAuth)
    @provides(AuthServ)
    def provide_auth_service(
        self,
        config,
        db,
        logger,
        facebook_auth,
        twitter_auth):
        return AuthService(
            config=config,
            db=db,
            logger=logger,
            facebook_auth=facebook_auth,
            twitter_auth=twitter_auth,
            session=session)

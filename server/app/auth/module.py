from flask import session
from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import AuthServ
from ..injector_keys import Config, Logging, SQLAlchemy
from .services import AuthService


class AuthModule(Module):

    @singleton
    @inject(config=Config,
            db=SQLAlchemy,
            logger=Logging)
    @provides(AuthServ)
    def provide_auth_service(
        self,
        config,
        db,
        logger):
        return AuthService(
            config=config,
            db=db,
            logger=logger,
            session=session)

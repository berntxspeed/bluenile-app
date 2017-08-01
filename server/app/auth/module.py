from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import AuthServ
from ..injector_keys import Config, Logging
from .services import AuthService


class AuthModule(Module):

    @singleton
    @inject(config=Config,
            logger=Logging)
    @provides(AuthServ)
    def provide_auth_service(self, config, logger):
        return AuthService(config=config, logger=logger)

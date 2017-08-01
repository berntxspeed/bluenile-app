from injector import Module
from injector import inject
from injector import provides

from .injector_keys import UserDataPushServ
from ..injector_keys import Config, Logging
from .services.data_push import UserDataPushService


class UserDataModule(Module):
    @inject(config=Config,
            logger=Logging)
    @provides(UserDataPushServ)
    def provides_user_data_push_service(self, config, logger):
        return UserDataPushService(config=config,
                                   logger=logger)

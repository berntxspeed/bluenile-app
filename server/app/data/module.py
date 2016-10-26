from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import DataPushServ
from ..injector_keys import Config, Logging, SQLAlchemy
from .services.data_push import DataPushService


class DataModule(Module):

    @singleton
    @inject(config=Config,
            db=SQLAlchemy,
            logger=Logging)
    @provides(DataPushServ)
    def provides_data_push_service(self, config, db, logger):
        return DataPushService(config=config,
                               db=db,
                               logger=logger)
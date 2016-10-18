from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import JbStatsServ, DataLoadServ
from ..injector_keys import Config, Logging, SQLAlchemy, MongoDB
from .services.jb_stats import JbStatsService
from .services.data_load import DataLoadService


class StatsModule(Module):

        @singleton
        @inject(config=Config,
                logger=Logging,
                db=SQLAlchemy,
                mongo=MongoDB)
        @provides(JbStatsServ)
        def provide_jb_stats_service(self, config, logger, db, mongo):
            return JbStatsService(config=config,
                                  logger=logger,
                                  db=db,
                                  mongo=mongo)

        @singleton
        @inject(config=Config,
                logger=Logging,
                db=SQLAlchemy,
                mongo=MongoDB)
        @provides(DataLoadServ)
        def provide_data_load_service(self, config, logger, db, mongo):
            return DataLoadService(config=config,
                                   logger=logger,
                                   db=db,
                                   mongo=mongo)

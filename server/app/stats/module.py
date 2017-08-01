from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import JbStatsServ, GetStatsServ, UserDataLoadServ
from ..injector_keys import Config, Logging, SQLAlchemy, MongoDB, DBSession
from .services.jb_stats import JbStatsService
from .services.get_stats import GetStatsService
from .services.data_load import UserDataLoadService


class StatsModule(Module):

        @singleton
        @inject(config=Config,
                logger=Logging,
                mongo=MongoDB)
        @provides(JbStatsServ)
        def provide_jb_stats_service(self, config, logger, mongo):
            return JbStatsService(config=config,
                                  logger=logger,
                                  mongo=mongo)

        @inject(config=Config,
                logger=Logging,
                db_session=DBSession)
        @provides(GetStatsServ)
        def provide_get_stats_service(self, config, logger, db_session):
            return GetStatsService(config=config,
                                   logger=logger,
                                   db_session=db_session)

        @inject(config=Config,
                logger=Logging,
                mongo=MongoDB)
        @provides(UserDataLoadServ)
        def provide_user_data_load_service(self, config, logger, mongo):
            return UserDataLoadService(config=config,
                                       logger=logger,
                                       mongo=mongo)

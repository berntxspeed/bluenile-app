from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import SqlQueryServ
from ..injector_keys import Config, Logging, SQLAlchemy
from .services.query_service import SqlQueryService


class SqlQueryModule(Module):

    @singleton
    @inject(config=Config,
            logger=Logging,
            db=SQLAlchemy)
    @provides(SqlQueryServ)
    def provide_sqlquery_service(self, config, logger, db):
        return SqlQueryService(config=config,
                               logger=logger,
                               db=db)

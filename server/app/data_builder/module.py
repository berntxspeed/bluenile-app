from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import SqlQueryServ
from ..injector_keys import Config, Logging, DBSession
from .services.query_service import SqlQueryService


class SqlQueryModule(Module):

    @inject(config=Config,
            logger=Logging,
            db_session=DBSession)
    @provides(SqlQueryServ)
    def provide_sqlquery_service(self, config, logger, db_session):
        return SqlQueryService(config=config,
                               logger=logger,
                               db_session=db_session)

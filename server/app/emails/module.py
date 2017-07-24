from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import EmailServ
from ..injector_keys import Config, Logging, DBSession
from .services.email_builder import EmailService


class EmailModule(Module):

    @inject(config=Config,
            logger=Logging,
            db_session=DBSession)
    @provides(EmailServ)
    def provide_email_service(self, config, logger, db_session):
        return EmailService(config=config,
                            logger=logger,
                            db=db_session)

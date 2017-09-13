from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import EmailServ
from ..injector_keys import Config, Logging, DBSession, MongoDB
from .services.email_builder import EmailService


class EmailModule(Module):

    @inject(config=Config,
            logger=Logging,
            mongo=MongoDB,
            db_session=DBSession)
    @provides(EmailServ)
    def provide_email_service(self, config, logger, mongo, db_session):
        return EmailService(config=config,
                            logger=logger,
                            mongo=mongo,
                            db_session=db_session)

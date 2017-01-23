from injector import Module
from injector import inject
from injector import provides
from injector import singleton

from .injector_keys import EmailServ
from ..injector_keys import Config, Logging, SQLAlchemy
from .services.email_builder import EmailService


class EmailModule(Module):

    @singleton
    @inject(config=Config,
            logger=Logging,
            db=SQLAlchemy)
    @provides(EmailServ)
    def provide_email_service(self, config, logger, db):
        return EmailService(config=config,
                               logger=logger,
                               db=db)
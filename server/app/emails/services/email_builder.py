from ...common.services import DbService
from ...common.models import Artist, Customer

class EmailService(DbService):

    def __init__(self, config, db, logger):
        super(EmailService, self).__init__(config, db, logger)

    def placeholder_func(self):
        pass
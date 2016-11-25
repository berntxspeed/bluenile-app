from .classes.data_pusher import DataPusher
from ...common.services import DbService
from ...common.models import Artist, Customer


class DataPushService(DbService):
    def __init__(self, config, db, logger):
        super(DataPushService, self).__init__(config, db, logger)
        self._models = {
            'artist': Artist,
            'customer': Customer
        }

    def sync_data_to_mc(self, table):
        if table not in self._models.keys():
            self.logger.warn('error, selected table is not available for mc sync')

        dp = DataPusher(self.db, self._models[table])
        resp = dp.sync_table()
        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))

    def clr_ext_sync_flags(self, table):
        if table not in self._models.keys():
            self.logger.warn('error, selected table is not available for this operation')

        try:
            model = self._models[table]
            for rec in model.query:
                rec._last_ext_sync = None
                self.db.session.add(rec)
            self.db.session.commit()
            self.logger.info('successfully cleared ext sync flags on all records')
        except:
            self.logger.warn('failure in resetting ext_sync_flags')

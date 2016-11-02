from flask import url_for
from flask import flash
from flask import redirect

from .classes.data_pusher import DataPusher
from ...common.services import DbService
from ...common.models import Artist, Customer, SendJob, EmlSend, EmlOpen, EmlClick


class DataPushService(DbService):

    def __init__(self, config, db, logger):
        super(DataPushService, self).__init__(config, db, logger)
        self._models = {
            'artist': Artist,
            'customer': Customer
        }

    def sync_data_to_mc(self, table):
        if table not in self._models.keys():
            flash('error, selected table is not available for mc sync')
            return redirect(url_for('data.test_page'))

        dp = DataPusher(self.db, self._models[table])
        resp = dp.sync_table()
        if resp and hasattr(resp, 'code'):
            flash('sync result:' + str(resp.code))
        else:
            flash('error with sync, see logs')
            flash(str(resp))
        return redirect(url_for('data.test_page'))
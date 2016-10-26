from flask import url_for
from flask import flash
from flask import redirect

from .classes.data_pusher import DataPusher
from ...common.services import DbService


class DataPushService(DbService):

    def __init__(self, config, db, logger):
        super(DataPushService, self).__init__(config, db, logger)

    def test(self):
        flash('ran test')
        return redirect(url_for('data.test_page'))
from flask import url_for
from werkzeug.utils import redirect

from . import data
from ..common.views.decorators import templated


@data.route('/data-pusher')
@templated('data_pusher')
def data_pusher():
    return {}


@data.route('/sync-data-to-mc/<table>')
def sync_data_to_mc(table):
    from .workers import sync_mc_data
    sync_mc_data.delay(table)
    # data_push_service.sync_data_to_mc(table)
    return redirect(url_for('data.data_pusher'))


@data.route('/clear-sync-flags/<table>')
def clr_ext_sync_flags(table):
    from .workers import clean_sync_flags
    clean_sync_flags.delay(table)
    return redirect(url_for('data.data_pusher'))

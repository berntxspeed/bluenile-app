from json import dumps

from flask import Response
from json import dumps

from . import data
from ..common.views.decorators import templated


@data.route('/data-pusher')
@templated('data_pusher')
def data_pusher():
    return {}


@data.route('/sync-data-to-mc/<table>')
@templated('data_pusher')
def sync_data_to_mc(table):
    from .workers import sync_data_to_mc
    result = sync_data_to_mc.delay(table)
    return dict(task_id=result.id)


@data.route('/clear-sync-flags/<table>')
@templated('data_pusher')
def clr_ext_sync_flags(table):
    from .workers import clean_sync_flags
    result = clean_sync_flags.delay(table)
    return dict(task_id=result.id)

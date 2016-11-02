from flask import request
from flask import session
from flask import Response
from flask_login import login_required
from injector import inject

from . import data
from .injector_keys import DataPushServ
from ..common.views.decorators import templated

@data.route('/data-pusher')
@templated('data_pusher')
def data_pusher():
    return {}

@data.route('/sync-data-to-mc/<table>')
@inject(data_push_service=DataPushServ)
def sync_data_to_mc(data_push_service, table):
    return data_push_service.sync_data_to_mc(table)

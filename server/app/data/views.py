from flask import request
from flask import session
from flask import Response
from flask_login import login_required
from injector import inject

from . import data
from .injector_keys import DataPushServ
from ..common.views.decorators import templated

@data.route('/test-page')
@templated('test_page')
def test_page():
    return {}


@data.route('/test')
@inject(data_push_service=DataPushServ)
def test(data_push_service):
    return data_push_service.test()
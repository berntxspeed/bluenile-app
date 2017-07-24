from flask import Response, request, redirect
from flask_login import login_required
from injector import inject
from json import dumps

from . import data
from ..common.views.decorators import templated
from ...app.injector_keys import MongoDB, UserSessionConfig

from ..data_builder.services.data_builder_query import DataBuilderQuery

# Pass this function to require login for every request
@data.before_request
@login_required
def before_request():
    pass

@data.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@data.route('/data-pusher')
@data.route('/data-pusher/<query_id>')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
@templated('data_pusher')
def data_pusher(mongo, user_config):
    status, result = DataBuilderQuery(mongo.db, user_config).get_all_queries(type='all')
    return dict(query_names=[ a_query['name'] for a_query in result ])


@data.route('/clear-sync-flags/<table>')
@inject(user_config=UserSessionConfig)
@templated('data_pusher')
def clr_ext_sync_flags(table, user_config):
    from .workers import clean_sync_flags
    result = clean_sync_flags.delay(table, user_params=user_config)
    return dict(task_id=result.id)


@data.route('/sync-query-to-mc/<query_name>')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
@templated('data_pusher')
def sync_query_to_mc(mongo, user_config, query_name):
    all_q_status, all_q_result = DataBuilderQuery(mongo.db, user_config).get_all_queries(type='all')
    status, query_rules = DataBuilderQuery(mongo.db, user_config).get_query_by_name(query_name)

    from .workers import sync_query_to_mc

    result = sync_query_to_mc.delay(query_rules, user_params=user_config, task_type='data-push', query_name=query_name)
    return dict(task_id=result.id, query_names=[a_query['name'] for a_query in all_q_result])

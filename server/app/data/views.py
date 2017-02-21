from flask import Response
from flask_login import login_required
from injector import inject
from json import dumps

from . import data
from ..common.views.decorators import templated
from ...app.injector_keys import MongoDB

from ..data_builder.services.data_builder_query import DataBuilderQuery

# Pass this function to require login for every request
@data.before_request
@login_required
def before_request():
    pass


@data.route('/data-pusher')
@data.route('/data-pusher/<query_id>')
@inject(mongo=MongoDB)
@templated('data_pusher')
def data_pusher(mongo):
    status, result = DataBuilderQuery(mongo.db).get_all_queries()
    return dict(query_names=[ a_query['name'] for a_query in result ])


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


@data.route('/sync-query-to-mc/<query_name>')
@inject(mongo=MongoDB)
@templated('data_pusher')
def sync_query_to_mc(mongo, query_name):
    all_q_status, all_q_result = DataBuilderQuery(mongo.db).get_all_queries()
    status, query_rules = DataBuilderQuery(mongo.db).get_query_by_name(query_name)

    from .workers import sync_query_to_mc
    result = sync_query_to_mc.delay(query_rules)
    return dict(task_id=result.id, query_names=[ a_query['name'] for a_query in all_q_result])
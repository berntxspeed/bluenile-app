import json

from flask import Response
from flask import request
from injector import inject

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import SQLAlchemy, MongoDB
from . import databuilder
from .services.data_builder_query import DataBuilderQuery

from .query_utils import get_customer_query_based_on_rules, extract_data,\
    map_models_to_columns, alchemy_encoder


@databuilder.route('/data-builder/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def data_builder(mongo, query_id):
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView, Artist]

    result = map_models_to_columns(models)

    status, data = DataBuilderQuery(mongo.db).get_query_by_name(query_id)

    return {'model': result, 'data': data, 'status': status}


# @databuilder.route('/get-query/<query_id>')
# @inject(mongo=MongoDB)
# def get_query(mongo, query_id):
#     status, result = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
#     return Response(json.dumps(result), mimetype='application/json')

@databuilder.route('/get-query/<query_id>')
@inject(mongo=MongoDB)
def get_query(mongo, query_id):
    status, result = DataBuilderQuery(mongo.db).get_all_queries()
    columns = [{
        'field': 'name',
        'title': 'Query Name'
        },
        {
        'field': 'created',
        'title': 'Created'
        }]
    return Response(json.dumps({'columns': columns, 'data': result}, default=alchemy_encoder),
                    mimetype='application/json')


@databuilder.route('/get-query/preview')
@inject(mongo=MongoDB)
def preview(mongo, query_id):
    status, _ = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
    return Response(json.dumps(result), mimetype='application/json')


@databuilder.route('/save-query/<query_id>', methods=['POST'])
@inject(mongo=MongoDB)
def save_query(mongo, query_id):
    # get user_id from session: for now saves only _csrf_token

    query = request.json
    success, error = DataBuilderQuery(mongo.db).save_query(query_id, query)
    if success:
        return 'OK', 200
    else:
        return error, 500


# @databuilder.route('/get-queries')
# @inject(mongo=MongoDB)
# def get_queries(mongo):
#     status, result = DataBuilderQuery(mongo.db).get_all_queries()
#     return json.dumps(result)


@databuilder.route('/query-preview', methods=['GET', 'POST'])
@inject(alchemy=SQLAlchemy)
def query_preview(alchemy):
    rules_query = request.json
    default_sql_query = alchemy.session.query(Customer)
    final_query = get_customer_query_based_on_rules(default_sql_query, rules_query)

    results = final_query.limit(100).all()
    columns, data = extract_data(results)
    return Response(json.dumps({'columns': columns, 'data': data}, default=alchemy_encoder),
                    mimetype='application/json')
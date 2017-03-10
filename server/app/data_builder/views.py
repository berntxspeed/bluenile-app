import json
import traceback

from flask import Response
from flask import request
from injector import inject

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import MongoDB
from .injector_keys import SqlQueryServ
from . import databuilder
from .services.data_builder_query import DataBuilderQuery
from .services.query_service import SqlQueryService


@databuilder.route('/data-builder/')
@databuilder.route('/data-builder/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def data_builder(mongo, query_id=None):
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView]

    result = SqlQueryService.map_models_to_columns(models)
    status, data = DataBuilderQuery(mongo.db).get_query_by_name(query_id)

    return {'model': result, 'data': data, 'status': status}


@databuilder.route('/get-queries')
@inject(mongo=MongoDB)
def get_queries(mongo):
    status, result = DataBuilderQuery(mongo.db).get_all_queries()
    columns = [{
            'field': 'name',
            'title': 'Query Name'
        },
        {
            'field': 'created',
            'title': 'Created'
        }]
    return Response(json.dumps({'columns': columns, 'data': result}, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')


@databuilder.route('/get-default-queries')
@inject(mongo=MongoDB)
def get_default_queries(mongo):
    status, result = DataBuilderQuery(mongo.db).get_all_queries(default=True)
    columns = [{
        'field': 'name',
        'title': 'Query Name'
        }]
    return Response(json.dumps({'columns': columns, 'data': result}, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')


@databuilder.route('/get-query/<query_id>')
@inject(mongo=MongoDB)
def get_query(mongo, query_id):
    status, result = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
    return Response(json.dumps(result), mimetype='application/json')


@databuilder.route('/delete-query/<query_id>', methods=['POST'])
@inject(mongo=MongoDB)
def delete_query(mongo, query_id):
    success, error = DataBuilderQuery(mongo.db).remove_query(query_id)
    if success:
        return 'OK', 200
    else:
        return error, 500


@databuilder.route('/save-query/<query_id>', methods=['POST'])
@inject(mongo=MongoDB)
def save_query(mongo, query_id):
    # TODO: get user_id from session: for now saves only _csrf_token
    query = request.json
    success, error = DataBuilderQuery(mongo.db).save_query(query_id, query)
    if success:
        return 'OK', 200
    else:
        return error, 500


@databuilder.route('/custom-query-preview/<query_sttmt>', methods=['POST'])
@inject(alchemy=SQLAlchemy)
def custom_query_preview(alchemy, query_sttmt):
    from sqlalchemy import func

    try:
        results = eval('alchemy.session.' + query_sttmt +'.limit(100).all()')
        rows_count = eval('alchemy.session.' + query_sttmt +'.count()')
        columns, data = SqlQueryService.extract_data(results, {})
        return Response(json.dumps({'columns': columns,
                                    'data': data,
                                    'no_of_rows': rows_count,
                                    }, default=SqlQueryService.alchemy_encoder),
                        mimetype='application/json')

    except Exception:
        return Response(json.dumps({'error_msg': traceback.format_exc(),
                                    }, default=SqlQueryService.alchemy_encoder),
                        mimetype='application/json')

@databuilder.route('/query-preview', methods=['POST'])
@inject(sql_query_service=SqlQueryServ)
def query_preview(sql_query_service):
    rules_query = request.json
    final_query = sql_query_service.get_customer_query_based_on_rules(rules_query)

    results = final_query.limit(100).all()
    columns, data = sql_query_service.extract_data(results, rules_query)
    return Response(json.dumps({'columns': columns,
                                'data': data,
                                'no_of_rows': final_query.count()
                                }, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')

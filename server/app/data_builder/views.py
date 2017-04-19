import csv
import json
import traceback
from io import StringIO

from flask import Response
from flask import make_response, redirect, request, url_for
from flask_login import login_required
from injector import inject
from sqlalchemy import func

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import MongoDB
from .injector_keys import SqlQueryServ
from . import databuilder
from .services.data_builder_query import DataBuilderQuery
from .services.query_service import SqlQueryService


# Pass this function to require login for every request
@databuilder.before_request
@login_required
def before_request():
    pass

@databuilder.route('/data-builder/')
@databuilder.route('/data-builder/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def data_builder(mongo, query_id=None):
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView]

    result = SqlQueryService.map_models_to_columns(models)
    status, data = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
    response_dict = {'model': result, 'data': data, 'status': status}

    if request.args.get('sync') == 'True':
        from ..data.workers import sync_query_to_mc
        result = sync_query_to_mc.delay(data)
        response_dict.update({'task_id': result.id})

    return response_dict


@databuilder.route('/sync-query/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def sync_current_query_to_mc(mongo, query_id):
    return redirect(url_for('data_builder.data_builder', query_id=query_id, sync=True))

    # return {'model': model,
    #         'data': query_rules,
    #         'status': status,
    #         'task_id': result.id
    #         }


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
    status, result = DataBuilderQuery(mongo.db).get_all_queries(type='default')
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
    try:
        results = eval('alchemy.session.' + query_sttmt + '.distinct(Customer.id).limit(100).all()')
        rows_count = eval('alchemy.session.' + query_sttmt + '.distinct(Customer.id).count()')
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


@databuilder.route('/export/<query_name>', methods=['GET'])
@inject(alchemy=SQLAlchemy, mongo=MongoDB, sql_query_service=SqlQueryServ)
def export_query_result(alchemy, mongo, sql_query_service, query_name):
    status, result = DataBuilderQuery(mongo.db).get_query_by_name(query_name)
    if status is not True:
        # TODO: handle error
        pass
    if 'custom_sql' in result.keys():
        from sqlalchemy import func
        results = eval('alchemy.session.' + result['custom_sql'] + '.all()')
        columns, data = SqlQueryService.extract_data(results, {})
    else:
        final_query = sql_query_service.get_customer_query_based_on_rules(result)
        results = final_query.all()
        columns, data = sql_query_service.extract_data(results, result)

    ordered_column_titles = [column['title'] for column in columns]
    ordered_column_fields = [column['field'] for column in columns]

    csv_list = [ordered_column_titles]
    for row in data:
        csv_list.append([row.get(field) for field in ordered_column_fields])

    si = StringIO()
    cw = csv.writer(si)
    cw.writerows(csv_list)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=" + query_name + "_Customer_Data.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@databuilder.route('/query-preview', methods=['POST'])
@inject(sql_query_service=SqlQueryServ)
def query_preview(sql_query_service):
    rules_query = request.json
    final_query = sql_query_service.get_customer_query_based_on_rules(rules_query)

    results = final_query.distinct(Customer.id).limit(100).all()
    columns, data = sql_query_service.extract_data(results, rules_query)
    return Response(json.dumps({'columns': columns,
                                'data': data,
                                'no_of_rows': final_query.distinct(Customer.id).count()
                                }, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')


@databuilder.route('/request-explore-values', methods=['POST'])
@inject(db=SQLAlchemy)
def request_explore_values(db):
    rules_query = request.json
    expression = rules_query.get('expression')
    get_results_query = 'db.session.query({0}, func.count({0}).label("total")).' \
                        'group_by({0}).order_by("total DESC").all()'.format(expression)
    results = eval(get_results_query)
    if (None, 0) in results:
        results.remove((None, 0))
    db.session.close()

    return Response(json.dumps([dict(value=result[0], count=result[1]) for result in results]),
                    mimetype='application/json')
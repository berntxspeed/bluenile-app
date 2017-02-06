import decimal
import json

from flask import Response
from flask import request
from injector import inject
from sqlalchemy import inspect
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import SQLAlchemy, MongoDB
from . import databuilder
from .services.data_builder_query import DataBuilderQuery

from server.app.data_builder.query_utils import get_customer_query_based_on_rules


@databuilder.route('/data-builder/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def data_builder(mongo, query_id):
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView, Artist]

    result = map_models_to_columns(models)

    status, data = DataBuilderQuery(mongo.db).get_query_by_name(query_id)

    return {'model': result, 'data': data, 'status': status}


@databuilder.route('/get-query/<query_id>')
@inject(mongo=MongoDB)
def get_query(mongo, query_id):
    status, result = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
    return Response(json.dumps(result), mimetype='application/json')


@databuilder.route('/get-query/preview')
@inject(mongo=MongoDB)
def preview(mongo, query_id):
    status, result = DataBuilderQuery(mongo.db).get_query_by_name(query_id)
    return Response(json.dumps(result), mimetype='application/json')


@databuilder.route('/save-query/<query_id>', methods=['POST'])
@inject(mongo=MongoDB)
def save_query(mongo, query_id):
    query = request.json
    success, error = DataBuilderQuery(mongo.db).save_query(query_id, query)
    if success:
        return 'OK', 200
    else:
        return error, 500


@databuilder.route('/get-queries')
@inject(mongo=MongoDB)
def get_queries(mongo):
    status, result = DataBuilderQuery(mongo.db).get_all_queries()
    return json.dumps(result)


def map_name_to_header(column_name):
    column_header_map = {
        'created_at': 'Created',
        'customer_id': 'Customer ID',
        'email_address': 'Email Address',
        'hashed_email': 'Hashed Email',
        'fname': 'First Name',
        'lname': 'Last Name',
        'marketing_allowed': 'Marketing Allowed',
        'purchase_count': 'Purchase Count',
        'total_spent_so_far': 'Total Spent'
    }
    return column_header_map.get(column_name, '')


def extract_data(results):
    model_columns = inspect(Customer).columns
    columns_list = []
    for column in model_columns:
        if column.key.startswith("_"): continue
        columns_list.append({
            'field': column.key,
            'title': map_name_to_header(column.name),
            'type': type_mapper(column.type)
        })
    data_list = []
    for customer in results:
        data_list.append(customer.__dict__)

    return columns_list, data_list


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


def alchemy_encoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def map_models_to_columns(models):
    result = dict()
    for model in models:
        columns = inspect(model).columns
        field_dict = dict()
        for column in columns:
            if column.key.startswith("_"): continue
            field_dict[column.key] = {
                'key': column.key,
                'name': column.name,
                'table': model.__name__,
                'expression': model.__name__ + '.' + column.name,
                'type': type_mapper(column.type)
            }

        result[model.__name__] = field_dict
    return result


def type_mapper(column_type):
    if (column_type.python_type is datetime) or isinstance(column_type, TIMESTAMP):
        return 'datetime'
    if (column_type.python_type is int) or isinstance(column_type, Integer):
        return 'integer'
    if column_type.python_type is float:
        return 'double'
    if column_type.python_type is bool:
        return 'boolean'
    return 'string'

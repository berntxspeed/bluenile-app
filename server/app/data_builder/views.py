import decimal
import json

from flask import Response
from flask import request
from injector import inject
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import inspect
from sqlalchemy import or_, and_
from sqlalchemy.sql.operators import ColumnOperators

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import SQLAlchemy, MongoDB
from . import databuilder
from .services.data_builder_query import DataBuilderQuery


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


@databuilder.route('/data-builder/<query_id>')
@inject(mongo=MongoDB)
@templated('data_builder')
def data_builder(mongo, query_id):
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView, Artist]

    result = map_models_to_columns(models)

    status, data = DataBuilderQuery(mongo.db).get_query_by_name(query_id)

    return {'model': result, 'data': data, 'status': status}


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
    # TODO: handle empty query: return all list of all customers

    query = request.json
    default_sql_query = alchemy.session.query(Customer)
    if query.get('rules', None):
        joined_query_obj, filter_exp = get_joined_query_obj(alchemy, query)
        final_query = joined_query_obj.filter(filter_exp)
    else:
        final_query = default_sql_query

    results = final_query.limit(100).all()
    columns, data = extract_data(results)
    return Response(json.dumps({'columns': columns, 'data': data}, default=alchemy_encoder),
                    mimetype='application/json')


def get_all_ids(rules):
    all_ids = set()
    for a_rule in rules.get('rules', []):
        if 'condition' in a_rule:
            all_ids = all_ids.union(get_all_ids(a_rule))
        else:
            all_ids.add(a_rule['id'])
    return all_ids


def get_filter(rule):
    models_map, _ = get_model_relations()
    model_name, column = rule['id'].split('.')
    model = models_map[model_name]['class']
    operator = rule['operator']
    condition = rule['value']

    operator_lookup = {'equal': ColumnOperators.__eq__,
                       'contains': ColumnOperators.like,
                       'begins_with': ColumnOperators.startswith,
                       'not_equal': ColumnOperators.__ne__,
                       'in': ColumnOperators.in_,
                       'not_in': ColumnOperators.notin_,
                       'ends_with': ColumnOperators.endswith,
                       # 'less or equal': ColumnOperators.__le__,
                       'greater': ColumnOperators.__gt__,
                       # 'greater or equal': ColumnOperators.__ge__,
                       'less': ColumnOperators.__lt__,
                       'between': ColumnOperators.between
                       }
    # TODO: implement 'not between', 'is null', 'is not null', etc.
    op = operator_lookup.get(operator, None)
    if op is None:
        raise Exception("Operator {0} not implemented".format(operator))
    # Get model class
    return op(getattr(model, column), condition)


def get_all_filters(rules):
    func_args = list()
    for a_rule in rules['rules']:
        if 'condition' in a_rule:
            func_args.append(get_all_filters(a_rule))
        else:
            func_args.append(get_filter(a_rule))

    if rules['condition'] == 'OR':
        return or_(*func_args)
    elif rules['condition'] == 'AND':
        return and_(*func_args)


def get_joined_query_obj(alchemy, query):
    models_map, class_relations = get_model_relations()
    joined_query = alchemy.session.query(Customer)
    all_ids = get_all_ids(query.get('rules', {}))
    filter_exp = get_all_filters(query.get('rules', {}))

    for an_id in all_ids:
        model, column = an_id.split('.')
        if model == 'Customer': continue
        rel_class, rel_column = class_relations[model].split('.')
        joined_query = joined_query.join(models_map[model]['class'],
                                         getattr(models_map[rel_class]['class'], rel_column))

    return joined_query, filter_exp


def get_model_relations():
    models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
              WebTrackingEcomm, WebTrackingPageView, Artist]

    def get_columns_map(model):
        columns = inspect(model).columns
        cols_dict = dict()
        for column in columns:
            if column.key.startswith("_"): continue
            col_sub_name = '"' + column.key + '"' if column.key[0].isupper() else column.key
            cols_dict[column.key] = col_sub_name
        return cols_dict

    models_map = dict()
    for a_model in models:
        models_map[a_model.__name__] = {
            'class': a_model,
            'tablename': a_model.__tablename__,
            'columns_map': get_columns_map(a_model)
        }

    model_relations = dict([(relation.mapper.class_.__name__, str(relation))
                            for relation in inspect(Customer).relationships])
    return models_map, model_relations


def alchemy_encoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)

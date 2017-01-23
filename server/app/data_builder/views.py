import datetime
import json
import pprint

from flask import Response
from injector import inject
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import inspect

from server.app.common.models import *
from server.app.common.views.decorators import templated
from . import databuilder
from .services.data_builder_query import DataBuilderQuery
from server.app.injector_keys import SQLAlchemy, MongoDB


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


@databuilder.route('/data-builder')
# @inject(db=SQLAlchemy)
@templated('data_builder')
def data_builder():
    result = dict()

    for model in [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
                  WebTrackingEcomm, WebTrackingPageView, Artist]:
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
    print(pprint.pprint(result))

    return {'model': result}


@databuilder.route('/build-tables')
@inject(db=SQLAlchemy)
def table_builder(db):
    result = {
        'selected_tables': [
            'Customer', 'EmlOpen', 'EmlClick'
        ],
        'rules': {
            'condition': 'AND',
            'rules': [
                {
                    'id': 'Customer.fname',
                    'operator': 'equal',
                    'value': "Bernt"
                }, {
                    'condition': 'OR',
                    'rules': [
                        {
                            'id': 'EmlOpen.EmailAddress',
                            'operator': 'equal',
                            'value': "bernt@bluenilesw.com"
                        }, {
                            'id': 'EmlClick.City',
                            'operator': 'equal',
                            'value': "San Fancisco"
                        }
                    ]
                }
            ]
        }
    }
    return Response(json.dumps(result), mimetype='application/json')


@databuilder.route('/get-queries')
@inject(mongo=MongoDB)
def get_queries(mongo):
    status, result = DataBuilderQuery(mongo.db).get_all_queries()
    return json.dumps(result)

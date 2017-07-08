import decimal
import re

from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import inspect

from .classes.sql_query_construct import SqlQueryConstructor
from ...common.models import *
from ...common.services import DbService


class SqlQueryService(object):

    def __init__(self, config, db_session, logger):
        self.config = config
        self.db_session = db_session
        self.logger = logger

    def get_customer_query_based_on_rules(self, rules_query):
        composed_query = SqlQueryConstructor(self.db_session, rules_query).construct_sql_query()
        return composed_query

    @staticmethod
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
        return column_header_map.get(column_name, column_name)

    @staticmethod
    def extract_data(results, query_rules):
        # Get all Customer columns
        columns_list = []
        model_columns = inspect(Customer).columns
        for column in model_columns:
            if column.key.startswith("_"): continue
            columns_list.append({
                'field': column.key,
                'title': SqlQueryService.map_name_to_header(column.name),
                'type': SqlQueryService.type_mapper(column.type)
            })

        # Get other selected columns
        models_map, _ = SqlQueryConstructor.get_db_model_relations()
        model_relations = SqlQueryConstructor.get_model_relations_from_rule(query_rules.get('rules', {}))
        # TODO: aggregate class names, e.g. to avoid multiple class inspection
        # TODO: universalize column names, akin to filter name universalization
        for model_relation in model_relations:
            class_name, column_name = model_relation.split('.')
            if class_name == 'Customer': continue
            model_columns = inspect(models_map[class_name]['class']).columns
            for column in model_columns:
                if column.key != column_name: continue
                columns_list.append({
                    'field': column.key,
                    'title': SqlQueryService.map_name_to_header(column.name),
                    'type': SqlQueryService.type_mapper(column.type)
                })

        # Get Data List
        data_list = []
        for a_result in results:
            data_dict = {}
            if isinstance(a_result, tuple):
                for data_row in a_result:
                    data_dict.update(data_row.__dict__)
            else:
                data_dict.update(a_result.__dict__)
            data_list.append(data_dict)

        return columns_list, data_list

    @staticmethod
    def user_friendly_filter_label(table_name, column_name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', table_name + ': ' + column_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower().replace('_', ' ').title()

    @staticmethod
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
                    'type': SqlQueryService.type_mapper(column.type),
                    'label': SqlQueryService.user_friendly_filter_label(model.__name__, column.name)
                }

            result[model.__name__] = field_dict
        return result

    @staticmethod
    def alchemy_encoder(obj):
        """JSON encoder function for SQLAlchemy special classes."""
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)

    @staticmethod
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


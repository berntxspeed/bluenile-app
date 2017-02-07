import decimal
from sqlalchemy import Integer
from sqlalchemy import TIMESTAMP
from sqlalchemy import inspect
from sqlalchemy import or_, and_
from sqlalchemy.sql.operators import ColumnOperators,\
    like_op, notcontains_op, notbetween_op, notendswith_op, notstartswith_op

from server.app.common.models import *


def get_customer_query_based_on_rules(default_sql_query, rules_query):
    if rules_query.get('rules', None):
        filter_expression = get_joined_query_obj(default_sql_query, rules_query)
        final_query = default_sql_query.filter(filter_expression)
    else:
        final_query = default_sql_query

    return final_query


def get_joined_query_obj(basic_customer_query, query_rules):
    models_map, class_relations = get_db_model_relations()
    model_relations = get_model_relations_from_rule(query_rules.get('rules', {}))

    for a_relation in model_relations:
        model, column = a_relation.split('.')
        if model == 'Customer': continue
        rel_class, rel_column = class_relations[model].split('.')
        basic_customer_query.join(models_map[model]['class'],
                                  getattr(models_map[rel_class]['class'], rel_column))

    filter_exp = get_all_filters(query_rules.get('rules', {}), models_map)
    return filter_exp


def get_model_relations_from_rule(rules):
    model_relations = set()
    for a_rule in rules.get('rules', []):
        if 'condition' in a_rule:
            model_relations = model_relations.union(get_model_relations_from_rule(a_rule))
        else:
            model_relations.add(a_rule['id'])
    return model_relations


def get_filter(rule, models_map):
    model_name, column = rule['id'].split('.')
    model = models_map[model_name]['class']
    operator = rule['operator']
    condition = rule['value']

    operator_lookup = {'equal': ColumnOperators.__eq__,
                       #TODO: change like to ilike?
                       'contains': ColumnOperators.contains,
                       'not_contains': lambda col, cond: col.operate(notcontains_op, cond),
                       'begins_with': ColumnOperators.startswith,
                       'not_begins_with': lambda col, cond: col.operate(notstartswith_op, cond),
                       'not_equal': ColumnOperators.__ne__,
                       'in': ColumnOperators.in_,
                       'not_in': ColumnOperators.notin_,
                       'ends_with': ColumnOperators.endswith,
                       'not_ends_with': lambda col, cond: col.operate(notendswith_op, cond),
                       'greater': ColumnOperators.__gt__,
                       'greater_or_equal': ColumnOperators.__ge__,
                       'less': ColumnOperators.__lt__,
                       'less_or_equal': ColumnOperators.__le__,
                       'between': lambda col, cond: col.between(*cond),
                       'not_between': lambda col, cond: col.operate(notbetween_op, *cond),
                       'is_empty': lambda col, cond: col.operate(like_op, ''),
                       'is_not_empty': lambda col, cond: col.notlike(''),
                       'is_null': ColumnOperators.is_,
                       'is_not_null': ColumnOperators.isnot
                       }
    # TODO: implement 'not between', 'is null', 'is not null', etc.
    op = operator_lookup.get(operator, None)
    if op is None:
        raise Exception("Operator {0} not implemented".format(operator))

    return op(getattr(model, column), condition)


def get_all_filters(rules, models_map):
    condition_args = list()
    for a_rule in rules['rules']:
        if 'condition' in a_rule:
            condition_args.append(get_all_filters(a_rule, models_map))
        else:
            condition_args.append(get_filter(a_rule, models_map))

    if rules['condition'] == 'OR':
        return or_(*condition_args)
    elif rules['condition'] == 'AND':
        return and_(*condition_args)


def get_db_model_relations():
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


def alchemy_encoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


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
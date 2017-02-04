from sqlalchemy import or_, and_
from sqlalchemy import inspect
from sqlalchemy.sql.operators import ColumnOperators

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
                       'contains': ColumnOperators.cont,
                       'not_contains': ColumnOperators.notcontains,  # notilike?
                       'begins_with': ColumnOperators.startswith,
                       'not_begins_with': ColumnOperators.notstartswith,
                       'not_equal': ColumnOperators.__ne__,
                       'in': ColumnOperators.in_,
                       'not_in': ColumnOperators.notin_,
                       'ends_with': ColumnOperators.endswith,
                       'not_ends_with': ColumnOperators.notendswith,
                       'greater': ColumnOperators.__gt__,
                       'greater_or_equal': ColumnOperators.__ge__,
                       'less': ColumnOperators.__lt__,
                       'less_or_equal': ColumnOperators.__le__,
                       'between': ColumnOperators.between,
                       'not_between': ColumnOperators.notbetween,
                       'is_empty': ColumnOperators.isempty,
                       'is_not_empty': ColumnOperators.isnotempty,
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

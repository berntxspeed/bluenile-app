from sqlalchemy import inspect
from sqlalchemy import or_, and_
from sqlalchemy.sql.operators import ColumnOperators, \
    like_op, notcontains_op, notbetween_op, notendswith_op, notstartswith_op

from ....common.models import Customer, Purchase, EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, WebTrackingPageView, WebTrackingEvent


class SqlQueryConstructor(object):

    def __init__(self, db, rules_query, customer_only=False):
        self.db = db
        self.rules_query = rules_query
        self.customer_only = customer_only

    def construct_sql_query(self):
        if self.rules_query.get('rules', None):
            joined_query_obj, filter_expression = self.get_joined_query_and_filter()
            final_query = joined_query_obj.filter(filter_expression)
        else:
            final_query = self.db.session.query(Customer)

        return final_query

    def get_joined_query_and_filter(self):
        models_map, class_relations = SqlQueryConstructor.get_db_model_relations()
        model_relations = SqlQueryConstructor.get_model_relations_from_rule(self.rules_query.get('rules', {}))
        uniq_models = set([a_model.split('.')[0] for a_model in model_relations])

        if self.customer_only is True:
            tables = [Customer]
        else:
            query_tables = [models_map[a_model]['class'] for a_model in uniq_models]
            if 'Customer' not in uniq_models:
                query_tables.insert(0, models_map['Customer']['class'])
            tables = list(reversed(query_tables))

        basic_customer_query = self.db.session.query(*tables)

        for a_relation in uniq_models:
            model = a_relation.split('.')[0]
            if model == 'Customer': continue
            rel_class, rel_column = class_relations[model].split('.')
            basic_customer_query = basic_customer_query.join(models_map[model]['class'],
                                                             getattr(models_map[rel_class]['class'], rel_column))

        filter_exp = self.get_all_filters(self.rules_query.get('rules', {}), models_map)
        return basic_customer_query, filter_exp

    @staticmethod
    def get_model_relations_from_rule(rules):
        model_relations = set()
        if rules is None:
            return model_relations
        for a_rule in rules.get('rules', []):
            if 'condition' in a_rule:
                model_relations = model_relations.union(SqlQueryConstructor.get_model_relations_from_rule(a_rule))
            else:
                model_relations.add(a_rule['id'])
        return model_relations

    def get_filter(self, rule, models_map):
        model_name, column = rule['id'].split('.')
        model = models_map[model_name]['class']
        operator = rule['operator']
        condition = rule['value']

        operator_lookup = {'equal': ColumnOperators.__eq__,
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

    def get_all_filters(self, rules, models_map):
        condition_args = list()
        for a_rule in rules['rules']:
            if 'condition' in a_rule:
                condition_args.append(self.get_all_filters(a_rule, models_map))
            else:
                condition_args.append(self.get_filter(a_rule, models_map))

        if rules['condition'] == 'OR':
            return or_(*condition_args)
        elif rules['condition'] == 'AND':
            return and_(*condition_args)

    @staticmethod
    def get_db_model_relations():
        models = [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
                  WebTrackingEcomm, WebTrackingPageView]

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

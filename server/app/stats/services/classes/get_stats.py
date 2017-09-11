from sqlalchemy import func, cast, extract, Float, Date
from sqlalchemy.inspection import inspect
from ....common.utils.db_datatype_handler import convert_to_attr_datatype


class StatsGetter(object):

    def __init__(self, db_session, tbl, acceptable_tbls, grp_by=None, calculate=None, filters=None):
        # 'in' case expects a string representation of an array of strings like this = '['xss', 'sde', 'wer']'
        self._allowable_filter_ops = {
            'eq': lambda q, col, val: q.filter(col == convert_to_attr_datatype(col, val)),
            'neq': lambda q, col, val: q.filter(col != convert_to_attr_datatype(col,val)),
            'gt': lambda q, col, val: q.filter(col > convert_to_attr_datatype(col, val)),
            'gte': lambda q, col, val: q.filter(col >= convert_to_attr_datatype(col, val)),
            'lt': lambda q, col, val: q.filter(col < convert_to_attr_datatype(col, val)),
            'lte': lambda q, col, val: q.filter(col <= convert_to_attr_datatype(col, val)),
            'contains': lambda q, col, val: q.filter(col.contains(convert_to_attr_datatype(col, val))),
            'startswith': lambda q, col, val: q.filter(col.startswith(convert_to_attr_datatype(col,val))),
            'endswith': lambda q, col, val: q.filter(col.endsswith(convert_to_attr_datatype(col, val))),
            'isnull': lambda q, col, val: q.filter(col == None),
            'notnull': lambda q, col, val: q.filter(col != None),
            'in': lambda q, col, val: q.filter(col.in_([convert_to_attr_datatype(col, x) for x in val[1: len(val)-1].split(', ')]))
        }

        self._allowable_math_ops = {
            'plus': lambda q, left, right: q.add_columns(cast(left, Float) + cast(right, Float)),
            'minus': lambda q, left, right: q.add_columns(cast(left, Float) - cast(right, Float)),
            'times': lambda q, left, right: q.add_columns(cast(left, Float) * cast(right, Float)),
            'dividedby': lambda q, left, right: q.add_columns(cast(left, Float) / cast(right, Float))
        }

        self._allowable_aggregate_ops = {
            'sum': lambda field: func.sum(field),
            'average': lambda field: func.avg(field),
            'max': lambda field: func.max(field),
            'min': lambda field: func.min(field),
            'count': lambda field: func.count(field)
        }

        self._allowable_field_operations = {
            'day': lambda field: extract('day', field),
            'month': lambda field: extract('month', field),
            'year': lambda field: extract('year', field),
            'hour': lambda field: extract('hour', field),
            'minute': lambda field: extract('minute', field),
            'date': lambda field: cast(field, Date)
        }

        self._db_session = db_session
        self._tbl = tbl
        self._acceptable_tables = acceptable_tbls

        if grp_by is not None:
            self._grp_by = grp_by.split('-')
        else:
            self._grp_by = None

        if calculate is not None:
            self._calculate = calculate
        else:
            self._calculate = None

        self._filters = filters
        if self._tbl not in self._acceptable_tables.keys():
            raise ValueError('illegal table selection of: ' + self._tbl + '. This is not in the list of allowable tables')
        self._model = self._acceptable_tables.get(self._tbl)

        self._joins = []

    def _check_grp_by(self):
        # check for any joins that need to be applied
        for grp_by in self._grp_by:
            if '.' in grp_by:
                join_field = grp_by.split('.')[0]
                self._joins.append(getattr(self._model, join_field))

    def _check_filters(self):
        # check for any joins that need to be applied
        for filter in self._filters:
            if '.' in filter.get('name'):
                join_field = filter.get('name').split('.')[0]
                self._joins.append(getattr(self._model, join_field))

    def _check_aggregate_calculation(self):
        # check for any joins that need to be applied
        if '.' in self._calculate.get('left-operand-field'):
            join_field = self._calculate.get('left-operand-field').split('.')[0]
            self._joins.append(getattr(self._model, join_field))
        if '.' in self._calculate.get('right-operand-field'):
            join_field = self._calculate.get('right-operand-field').split('.')[0]
            self._joins.append(getattr(self._model, join_field))

    def _apply_joins(self, q):
        for join in self._joins:
            q = q.join(join)

        return q

    def _get_column(self, col_request):
        field = col_request
        field_op = None

        if ':' in col_request:
            field_op = col_request.split(':')[1]
            field = col_request.split(':')[0]
            if field_op in self._allowable_field_operations.keys():
                field_op = self._allowable_field_operations.get(field_op)
            else:
                raise ValueError('invalid field operation for field: ' + field)

        if '.' in col_request:
            print('field = ' + field)
            relationship_field = field.split('.')[0]
            field = field.split('.')[1]
            relationship_model = getattr(self._model, relationship_field).property.mapper.class_
            column = getattr(relationship_model, field)
        else:
            column = getattr(self._model, field)

        if field_op:
            return field_op(column)
        else:
            return column

    def _apply_filters_to_query(self, q):
        if self._filters is not None:
            for filter in self._filters:
                if filter.get('name') in [column['name'] for column in self.get_columns()]:
                    if filter.get('op') in self._allowable_filter_ops.keys():
                        column = self._get_column(filter.get('name'))
                        q = self._allowable_filter_ops.get(filter.get('op'))(q, column, filter.get('val'))
                        continue
                    raise ValueError('invalid data for filter definition: op')
                raise ValueError('invalid data for filter definition: name')
        return q

    def _apply_group_bys_to_query(self, q):
        if self._grp_by is not None:
            for grp_by in self._grp_by:
                column = self._get_column(grp_by)
                q = q.add_columns(column).group_by(column)
            return q

    def _apply_aggregate_calculation(self, q):
        left_op_field = self._calculate.get('left-operand-field', None)
        left_op_agg_op = self._calculate.get('left-operand-agg-op', None)
        right_op_field = self._calculate.get('right-operand-field', None)
        right_op_agg_op = self._calculate.get('right-operand-agg-op', None)
        math_op = self._calculate.get('math-op', None)
        left_op = None
        right_op = None

        if left_op_agg_op != 'count' and left_op_field is None:
            raise ValueError('must supply a field to aggregate by if first agg operation is not count')
        if right_op_agg_op != 'count' \
                and right_op_agg_op is not None \
                and right_op_field is None:
            raise ValueError('must supply a field to aggregate by if second agg operation is not count')

        if (math_op is not None and math_op != '' and (right_op_agg_op is None or right_op_agg_op == '') ) \
                or ( (math_op is None or math_op == '') and right_op_agg_op is not None and right_op_agg_op != ''):
            raise ValueError('must supply both math operation AND a second aggregate operation if a calculation is desired')

        if left_op_agg_op is not None:
            if left_op_agg_op in self._allowable_aggregate_ops.keys():
                if left_op_field is not None and left_op_field != '':
                    left_op_field = self._get_column(left_op_field)
                else:
                    left_op_field = '*'
                left_op = self._allowable_aggregate_ops.get(left_op_agg_op)(left_op_field)
            else:
                raise ValueError('invalid aggregate operation specified for first aggregate op')
        else:
            raise ValueError('must specify an aggregate operation')

        if right_op_agg_op is not None and right_op_agg_op != '':
            if right_op_agg_op in self._allowable_aggregate_ops.keys():
                if right_op_field is not None and right_op_field != '':
                    right_op_field = self._get_column(right_op_field)
                else:
                    right_op_field = '*'
                right_op = self._allowable_aggregate_ops.get(right_op_agg_op)(right_op_field)
            else:
                raise ValueError('invalid aggregate operation specified for second aggregate op')

        if math_op is not None and math_op != '':
            if left_op is not None and right_op is not None:
                if math_op in self._allowable_math_ops.keys():
                    q = self._allowable_math_ops.get(math_op)(q, left_op, right_op)
                else:
                    raise ValueError('invalid math operation specified')
            else:
                raise ValueError('in order to perform a math operation, must specify two operands')
        else:
            q = q.add_columns(left_op)

        return q

    def get(self):
        """
        Executes query and returns result
        """
        q = self._db_session.query()

        try:
            self._check_grp_by()
            self._check_filters()
            self._check_aggregate_calculation()
        except ValueError:
            raise ValueError('problem with group by and/or filters.  check api request.')

        if len(self._joins) > 0:
            q = self._apply_joins(q)

        q = self._apply_group_bys_to_query(q)
        q = self._apply_filters_to_query(q)
        q = self._apply_aggregate_calculation(q)

        return q.all()

    def get_columns(self):
        """
        Returns: a list of columns within the selected table
        and their data types
        """
        cols = []

        def add_col(column_name, column_type, rel_bool):
            if rel_bool:
                rel_bool = 'True'
            else:
                rel_bool = 'False'

            cols.append(dict(name=column_name,
                             type=column_type,
                             relationship=rel_bool))
            # add type-specific functions to columns
            if 'TIMESTAMP' in column_type:
                # add day/month/year/hour/min options
                cols.append(dict(name=column_name + ':date',
                                 type='DATE',
                                 relationship=rel_bool))
                cols.append(dict(name=column_name + ':day',
                                 type='INTEGER',
                                 relationship=rel_bool))
                cols.append(dict(name=column_name + ':month',
                                 type='INTEGER',
                                 relationship=rel_bool))
                cols.append(dict(name=column_name + ':year',
                                 type='INTEGER',
                                 relationship=rel_bool))
                cols.append(dict(name=column_name + ':hour',
                                 type='INTEGER',
                                 relationship=rel_bool))
                cols.append(dict(name=column_name + ':minute',
                                 type='INTEGER',
                                 relationship=rel_bool))

        for column, _ in self._model.__dict__.items():
            try:
                # add fields on the base table
                col_type = str(self._model.__table__.c[column].type)
                add_col(column, col_type, False)
            except:
                # add the fields on the related table of a relationship field, like SendJob.eml_clicks -> EmlClick
                if column in inspect(self._model).relationships.keys():
                    rel = inspect(self._model).relationships[column]
                    for rel_column in rel.target.columns.keys():
                        try:
                            rel_column_type = str(rel.target.c[rel_column].type)
                            add_col(column + '.' + rel_column, rel_column_type, True)
                        except:
                            pass
                else:
                    pass
        return cols

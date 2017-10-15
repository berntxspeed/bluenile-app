from sqlalchemy import func
import datetime

from ....common.utils.db_datatype_handler import convert_to_attr_datatype


class StatsGetter(object):

    def __init__(self, db_session, tbl, acceptable_tbls, grp_by=None, filters=None):
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
        self._db_session = db_session
        self._tbl = tbl
        self._acceptable_tables = acceptable_tbls

        if grp_by is not None:
            self._grp_by = grp_by.split('-')
        else:
            self._grp_by = None

        self._filters = filters
        if self._tbl not in self._acceptable_tables.keys():
            raise ValueError('illegal table selection of: ' + self._tbl + '. This is not in the list of allowable tables')
        self._model = self._acceptable_tables.get(self._tbl)

    def _check_grp_by(self):
        pass

    def _check_filters(self):
        pass

    def _apply_filters_to_query(self, q):
        if self._filters is not None:
            for filter in self._filters:
                if filter.get('name') in [column['name'] for column in self.get_columns()]:
                    if filter.get('op') in self._allowable_filter_ops.keys():
                        column = getattr(self._model, filter.get('name'))
                        q = self._allowable_filter_ops.get(filter.get('op'))(q, column, filter.get('val'))
                        continue
                    raise ValueError('invalid data for filter definition: op')
                raise ValueError('invalid data for filter definition: name')
        return q

    def _apply_group_bys_to_query(self, q):
        if self._grp_by is not None:
            for grp_by in self._grp_by:
                column = getattr(self._model, grp_by)
                q = q.add_columns(column).group_by(column)
            return q

    def get(self, aggregate_op, aggregate_field):
        """
        Executes query and returns result
        """
        try:
            self._check_grp_by()
            self._check_filters()
        except ValueError:
            raise

        q = self._db_session.query()

        q = self._apply_group_bys_to_query(q)
        q = self._apply_filters_to_query(q)

        if aggregate_op != 'count' and aggregate_field is None:
            raise ValueError('must supply a field to aggregate by if agg-operation is other than count')

        if aggregate_field is not None:
            agg_field = getattr(self._model, aggregate_field)
        else:
            agg_field = '*'

        agg_ops = {
            'sum': func.sum(agg_field),
            'average': func.avg(agg_field),
            'max': func.max(agg_field),
            'min': func.min(agg_field),
            'count': func.count(agg_field)
        }

        agg_op = agg_ops.get(aggregate_op, None)

        if agg_op is None:
            raise ValueError('invalid aggregate operation specified: '+aggregate_op)

        # sum, count, max, min, avg
        q = q.add_columns(agg_op)

        return q.all()

    def get_columns(self):
        """
        Returns: a list of columns within the selected table
        and their data types
        """
        cols = []
        for column, _ in self._model.__dict__.items():
            try:
                cols.append(dict(name=column,
                                 type=str(self._model.__table__.c[column].type)))
            except:
                pass
        return cols

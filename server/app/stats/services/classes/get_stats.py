from sqlalchemy import func
import datetime


class StatsGetter(object):

    def __init__(self, db, tbl, acceptable_tbls, grp_by=None, filters=None):
        self._allowable_filter_ops = {
            'eq': lambda q, col, val: q.filter(col == val),
            'gt': lambda q, col, val: q.filter(col > val),
            'lt': lambda q, col, val: q.filter(col < val),
            'date_gt': lambda q, col, val: q.filter(col > datetime.datetime.strptime(val, '%Y-%m-%d')),
            'date_lt': lambda q, col, val: q.filter(col < datetime.datetime.strptime(val, '%Y-%m-%d'))
        }
        self._db = db
        self._tbl = tbl
        self._acceptable_tables = acceptable_tbls
        self._grp_by = grp_by
        self._filters = filters
        if self._tbl not in self._acceptable_tables.keys():
            raise ValueError('illegal table selection of: ' + self._tbl + '. This is not in the list of allowable tables')
        self._model = self._acceptable_tables.get(self._tbl)

    def _check_grp_by(self):
        pass

    def _check_filters(self):
        pass

    def _apply_filters_to_query(self, q):
        for filter in self._filters:
            if filter.get('name') in self.get_columns():
                if filter.get('op') in self._allowable_filter_ops.keys():
                    if filter.get('val') != None:
                        column = getattr(self._model, filter.get('name'))
                        q = self._allowable_filter_ops.get(filter.get('op'))(q, column, filter.get('val'))
                        continue
                    raise ValueError('invalid data for filter definition: val')
                raise ValueError('invalid data for filter definition: op')
            raise ValueError('invalid data for filter definition: name')
        return q

    def get(self):
        """
        Executes query and returns result
        """
        try:
            self._check_grp_by()
            self._check_filters()
        except ValueError:
            raise
        model = self._model
        column = getattr(model, self._grp_by)
        q = self._db.session.query(column, func.count(column)).group_by(column)
        q = self._apply_filters_to_query(q)
        return q.all()

    def get_columns(self):
        """
        Returns: a list of columns within the selected table
        """
        cols = []
        for column, _ in self._model.__dict__.items():
            if column[0] != '_':
                cols.append(column)
        return cols

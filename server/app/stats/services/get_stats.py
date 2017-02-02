from flask import jsonify

from ...common.services import DbService
from ...common.models import Artist, Customer, EmlSend, EmlOpen, EmlClick
from .classes.get_stats import StatsGetter

class GetStatsService(DbService):

    def __init__(self, config, db, logger):
        super(GetStatsService, self).__init__(config, db, logger)
        self._acceptable_tables = {
            'Customer': Customer,
            'Artist': Artist,
            'EmlSend': EmlSend,
            'EmlOpen': EmlOpen,
            'EmlClick': EmlClick
        }

    def get_columns(self, tbl):
        """
        Returns: a list of columns for a table
        tbl = 'EmlOpen' # a table to query
        """
        try:
            st = StatsGetter(db=self.db,
                             tbl=tbl,
                             acceptable_tbls=self._acceptable_tables)
        except ValueError as exc:
            return jsonify(error=exc)

        return jsonify(columns=st.get_columns())

    def get_grouping_counts(self, tbl, grp_by, filters=None):
        """
        tbl = 'EmlOpen' # a table to query
        grp_by = 'Device' # a db field name to group by
            if multiple group bys are required = 'OperatingSystem-Device'
        filters=[
            {
                'field': 'EventDate',
                'op': 'gt',
                'val': '12/01/2016 11:59:00 PM'
            },{
                'field': 'EventDate',
                'op': 'lt',
                'val': '11/01/2016 11:59:00 PM'
            },{
                'field': 'SendID',
                'op': 'eq',
                'val': '23421'
            }
        ]
        """
        try:
            st = StatsGetter(db=self.db,
                             tbl=tbl,
                             acceptable_tbls=self._acceptable_tables,
                             grp_by=grp_by,
                             filters=filters)
            results = st.get()
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        return jsonify(results=results)

    def send_view(self):
        """
        uses self.get_grouping_counts to order and sort send results by number
        of sent/opens/clicks in descending order
        """
        st = StatsGetter(db=self.db,
                         tbl='EmlOpen',
                         acceptable_tbls=self._acceptable_tables,
                         grp_by='SendID',
                         filters=None)
        sends = st.get()
        sends.sort(key=lambda send: send[1], reverse=True)

        return {
            'sends': sends
        }

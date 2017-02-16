from flask import jsonify

from ...common.services import DbService
from ...common.models import Artist, Customer, EmlSend, EmlOpen, EmlClick, SendJob
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

        sends = SendJob.query.all()

        sends_by_emailname = {}
        sends_by_sendid = []

        for send in sends:
            print('processing sendid: ' + str(send.SendID))
            sends_by_sendid.append({
                'sendid': send.SendID,
                'email_name': send.EmailName,
                'num_sent': send.num_sends
            })
            if send.EmailName in sends_by_emailname.keys():
                sends_by_emailname.get(send.EmailName).get('sendids').append(send.SendID)
                sends_by_emailname.get(send.EmailName)['num_sendids'] += 1
                sends_by_emailname.get(send.EmailName)['num_sent'] += send.num_sends
            else:
                sends_by_emailname[send.EmailName] = {
                    'sendids': [send.SendID],
                    'num_sendids': 1,
                    'num_sent': send.num_sends
                }

        sends_by_sendid.sort(key=lambda send: send['num_sent'], reverse=True)


        return {
            'sends_by_sendid': sends_by_sendid,
            'sends_by_emailname': sends_by_emailname
        }

    def send_info(self, sendid):
        if sendid is not None:
            send = SendJob.query.filter(SendJob.SendID == sendid).first()
            if send is not None:
                return jsonify(emailName=send.EmailName,
                               numSends=send.num_sends,
                               numOpens=send.num_opens,
                               numClicks=send.num_clicks,
                               previewUrl=send.PreviewURL,
                               schedTime=send.SchedTime,
                               sentTime=send.SentTime,
                               subject=send.Subject), 200
            else:
                error = 'couldnt find that sendid: ' + str(sendid)
        else:
            error = 'must specify a sendid'
        return jsonify(error=error), 400




from flask import jsonify
from sqlalchemy import func

from ...common.models.user_models import Customer, Purchase, EmlSend, EmlOpen, EmlClick, SendJob, Event, \
    WebTrackingEvent, WebTrackingPageView, WebTrackingEcomm, Report
from .classes.get_stats import StatsGetter


class GetStatsService(object):
    def __init__(self, config, db_session, logger):
        self.config = config
        self.db_session = db_session
        self.logger = logger

        self._acceptable_tables = {
            'Customer': Customer,
            'Purchase': Purchase,
            'EmlSend': EmlSend,
            'EmlOpen': EmlOpen,
            'EmlClick': EmlClick,
            'WebTrackingPageView': WebTrackingPageView,
            'WebTrackingEvent': WebTrackingEvent,
            'WebTrackingEcomm': WebTrackingEcomm,
            'Event': Event,
            'SendJob': SendJob
        }

    @staticmethod
    def validate_on_submit(request, form):
        return request.method == 'POST' and form.validate()

    def get_columns(self, tbl):
        """
        Returns: a list of columns for a table
        tbl = 'EmlOpen' # a table to query
        """
        try:
            st = StatsGetter(db_session=self.db_session,
                             tbl=tbl,
                             acceptable_tbls=self._acceptable_tables)
        except ValueError as exc:
            return jsonify(error=str(exc)), 404

        columns = st.get_columns()
        return jsonify(columns=columns)


    def get_grouping_counts(self, tbl, grp_by, calculate, filters=None):
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
        calculate = {
            'left-operand-field': aggregateField,
            'left-operand-agg-op': aggregateOp,
            'right-operand-field': aggregateField2,
            'right-operand-agg-op': aggregateOp2,
            'math-op': mathOp
        }
        """
        try:
            st = StatsGetter(db_session=self.db_session,
                             tbl=tbl,
                             acceptable_tbls=self._acceptable_tables,
                             grp_by=grp_by,
                             calculate=calculate,
                             filters=filters)
            results = st.get()
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        return jsonify(results=results)

    def report_view(self):
        tables = self._acceptable_tables.keys()

        reports = self.db_session.query(Report).all()

        sends = self.db_session.query(SendJob).all()

        sends_by_emailname = {}
        sends_by_sendid = []

        for send in sends:
            # print('processing sendid: ' + str(send.SendID))

            if send.num_sends is not None and send.num_sends > 0:
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

        sends_w_mult_sendids = {}
        for key, value in sends_by_emailname.items():
            if value['num_sendids'] > 1:
                sends_w_mult_sendids[key] = value

        return {
            'sends_by_sendid': sends_by_sendid,
            'sends_by_emailname': sends_w_mult_sendids,
            'tables': tables,
            'reports': reports
        }

    def send_info(self, option, request):
        sendid = request.form.get('sendid', None)
        try:
            if sendid is not None and option in ['send-id', 'trig-send-id', 'mult-send-id']:
                if option == 'send-id':
                    if sendid[0] == '[':
                        sendid = sendid[1: len(sendid) - 1]
                    send = self.db_session.query(SendJob).filter(SendJob.SendID == sendid).first()
                elif option == 'trig-send-id':
                    eml_send = self.db_session.query(EmlSend).filter(EmlSend.TriggeredSendExternalKey == sendid).first()
                    if eml_send is None:
                        raise ValueError('no emails sent with that TriggeredSendExternalKey')
                    xsendid = eml_send.SendID
                    send = self.db_session.query(SendJob).filter(SendJob.SendID == xsendid).first()
                    # TODO: add check that a record was yielded from SendJob before proceeding
                    send.num_sends = \
                    self.db.session.query(func.count('*')).filter(EmlSend.TriggeredSendExternalKey == sendid).first()[0]
                    send.num_opens = \
                    self.db.session.query(func.count('*')).filter(EmlOpen.TriggeredSendExternalKey == sendid).filter(
                        EmlOpen.IsUnique == True).first()[0]
                    send.num_clicks = \
                    self.db.session.query(func.count('*')).filter(EmlClick.TriggeredSendExternalKey == sendid).filter(
                        EmlClick.IsUnique == True).first()[0]
                elif option == 'mult-send-id':
                    sends = self.db_session.query(SendJob).filter(SendJob.SendID.in_(sendid[1: len(sendid) - 1].split(', '))).all()
                    send = sends[0]
                    for xsend in sends[1:]:
                        send.num_sends += xsend.num_sends
                        send.num_opens += xsend.num_opens
                        send.num_clicks += xsend.num_clicks
                        if xsend.SchedTime < send.SchedTime:
                            send.SchedTime = xsend.SchedTime
                        if xsend.SentTime < send.SentTime:
                            send.SentTime = xsend.SentTime
                else:
                    raise ValueError('not a valid option for /send-info: ' + str(option))

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
                    raise ValueError('couldnt find that sendid: ' + str(sendid))
            else:
                raise ValueError('must specify a sendid:' + str(sendid) + ' and provide a valid option: ' + str(option))
        except Exception as exc:
            return jsonify(error=str(exc)), 400

    def save_report(self, rpt_id, rpt_name, graph_type, tbl, grp_by, calculate, filters=None):

        db_op = 'update'
        rpt = None

        if rpt_id is not None:
            rpt = self.db_session.query(Report).filter(Report.id == rpt_id).first()

        if rpt is None:
            db_op = 'add'
            rpt = Report()

        rpt.name = rpt_name
        rpt.table = tbl
        rpt.grp_by_first = grp_by.split('-')[0]

        try:
            rpt.grp_by_second = grp_by.split('-')[1]
        except:
            pass

        rpt.aggregate_op = calculate.get('left-operand-agg-op', None)
        rpt.aggregate_field = calculate.get('left-operand-field', None)
        rpt.aggregate_op_2 = calculate.get('right-operand-agg-op', None)
        rpt.aggregate_field_2 = calculate.get('right-operand-field', None)
        rpt.math_op = calculate.get('math-op', None)

        rpt.filters_json = filters

        rpt.graph_type = graph_type

        if db_op == 'add':
            self.db_session.add(rpt)
        elif db_op == 'update':
            self.db_session.merge(rpt)

        self.db_session.commit()

        return jsonify(reportId=rpt.id)

    def get_report(self, rpt_id):

        rpt = self.db_session.query(Report).filter(Report.id == rpt_id).first()

        if rpt is not None:
            report = dict(table=rpt.table,
                          id=rpt.id,
                          name=rpt.name,
                          grp_by_first=rpt.grp_by_first,
                          grp_by_second=rpt.grp_by_second,
                          aggregate_op=rpt.aggregate_op,
                          aggregate_field=rpt.aggregate_field,
                          aggregate_op_2=rpt.aggregate_op_2,
                          aggregate_field_2=rpt.aggregate_field_2,
                          math_op=rpt.math_op,
                          graph_type=rpt.graph_type,
                          filters_json=rpt.filters_json,
                          created=rpt.created,
                          last_modified=rpt.last_modified)
            return jsonify(report=report)
        else:
            return jsonify(error='report not found'), 404

    def delete_report(self, rpt_id):

        rpt = self.db_session.query(Report).filter(Report.id == rpt_id).first()

        if rpt is not None:
            try:
                self.db_session.delete(rpt)
                self.db_session.commit()
                return jsonify(status='deleted')
            except Exception as exc:
                return jsonify(error='problem deleting report'), 500

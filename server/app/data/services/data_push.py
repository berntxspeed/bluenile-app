from sqlalchemy import func

from .classes.data_pusher import DataPusher
from ...common.services import DbService
from ...common.models import Artist, Customer, Purchase, EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, WebTrackingPageView, WebTrackingEvent


class DataPushService(DbService):
    def __init__(self, config, db, logger):
        super(DataPushService, self).__init__(config, db, logger)
        self._models = {
            'artist': Artist,
            'customer': Customer
        }

    def sync_data_to_mc(self, table):
        if table not in self._models.keys():
            self.logger.warn('error, selected table is not available for mc sync')

        dp = DataPusher(self.db, self._models[table])
        resp = dp.sync_table()
        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))

    def clean_sync_flags(self, table):
        if table not in self._models.keys():
            self.logger.warn('error, selected table is not available for this operation')

        try:
            model = self._models[table]
            for rec in model.query:
                rec._last_ext_sync = None
                self.db.session.add(rec)
            self.db.session.commit()
            self.logger.info('successfully cleared ext sync flags on all records')
        except:
            self.logger.warn('failure in resetting ext_sync_flags')

    def sync_query_to_mc(self, query):

        query1 = self.db.session.query(Customer)\
            .join(Purchase, Customer.purchases)\
            .group_by(Customer.customer_id)\
            .having(func.count(Customer.purchases) >= 2)

        query2 = self.db.session.query(Customer) \
            .join(WebTrackingPageView, Customer.web_tracking_page_views) \
            .filter(WebTrackingPageView.page_path == '/products/widget-2') \
            .group_by(Customer.customer_id) \
            .having(func.count(Customer.web_tracking_page_views) >= 1)

        query3 = self.db.session.query(Customer) \
            .join(EmlClick, Customer.eml_clicks) \
            .group_by(Customer.customer_id) \
            .having(func.count(Customer.eml_clicks) >= 1)

        queries = {'query1': {'name': 'customers with 2 or more purchases', 'q': query1},
                   'query2': {'name': 'customers who viewed widget2 page on website', 'q': query2},
                   'query3': {'name': 'customers who clicked a marketing email', 'q': query3}}

        query = queries.get(query, None)

        if query is None:
            self.logger.warn('error, selected query is not available for mc sync: allowed queries: ' + str(queries.keys()))

        dp = DataPusher(self.db, self._models['customer'])
        resp = dp.sync_query(name=query['name'], query=query['q'])
        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))
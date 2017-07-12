import datetime
from sqlalchemy import func

from .classes.data_pusher import DataPusher
from ...common.services import DbService
from ...common.models.user_models import Customer, Purchase, EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, \
    WebTrackingPageView, WebTrackingEvent
from server.app.data_builder.services.classes.sql_query_construct import SqlQueryConstructor


class DataPushService(DbService):
    def __init__(self, config, db, logger):
        super(DataPushService, self).__init__(config, db, logger)
        self.db_session = self.db.session
        self._models = {
            'customer': Customer,
            'purchase': Purchase
        }

    def exec_safe_session(self, service_func=None, *args):
        if service_func:
            try:
                service_func(*args)
            except Exception as exc:
                self.db_session.rollback()
                raise type(exc)('Data Push Error: {0}: {1}'.format(type(exc).__name__, exc.args))
            finally:
                self.db_session.remove()

    def sync_data_to_mc(self, table):
        if table not in self._models.keys():
            self.logger.warn('error, selected table is not available for mc sync')

        dp = DataPusher(self.db_session, self._models[table])
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
                self.db_session.add(rec)
            self.db_session.commit()
            self.logger.info('successfully cleared ext sync flags on all records')
        except:
            self.logger.warn('failure in resetting ext_sync_flags')

    # TODO: Add another func to take query object

    def sync_query_to_mc(self, query_rules):

        # query1 = self.db_session.query(Customer)\
        #     .join(Purchase, Customer.purchases)\
        #     .group_by(Customer.customer_id)\
        #     .having(func.count(Customer.purchases) >= 2)
        #
        # query2 = self.db_session.query(Customer) \
        #     .join(WebTrackingPageView, Customer.web_tracking_page_views) \
        #     .filter(WebTrackingPageView.page_path == '/products/widget-2') \
        #     .group_by(Customer.customer_id) \
        #     .having(func.count(Customer.web_tracking_page_views) >= 1)
        #
        # query3 = self.db_session.query(Customer) \
        #     .join(EmlClick, Customer.eml_clicks) \
        #     .group_by(Customer.customer_id) \
        #     .having(func.count(Customer.eml_clicks) >= 1)

        # queries = {'query1': {'name': 'customers with 2 or more purchases', 'q': query1},
        #            'query2': {'name': 'customers who viewed widget2 page on website', 'q': query2},
        #            'query3': {'name': 'customers who clicked a marketing email', 'q': query3}}

        dp = DataPusher(self.db_session, self._models['customer'])
        resp = dp.sync_query(name=query_rules['name'],
                             query=SqlQueryConstructor(self.db_session, query_rules,
                                                       customer_only=True).construct_sql_query())

        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))


class UserDataPushService(DataPushService):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_session = None

        self._models = {
            'customer': Customer,
            'purchase': Purchase
        }

    def init_user_db(self, db_uri):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(db_uri)
        self.db_session = scoped_session(sessionmaker(bind=engine))

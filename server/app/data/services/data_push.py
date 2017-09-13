from server.app.data.services.classes.data_pusher import DataPusher
from server.app.common.models.user_models import Customer, Purchase, EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, \
    WebTrackingPageView, WebTrackingEvent
from server.app.data_builder.services.classes.sql_query_construct import SqlQueryConstructor
from server.app.stats.services.mongo_user_config_loader import MongoUserApiConfigLoader


class UserDataPushService:
    def __init__(self, config, logger, mongo):
        self.config = config
        self.logger = logger
        self.mongo = mongo
        self.db_session = None

        self._models = {
            'customer': Customer,
            'purchase': Purchase
        }
        self.user_api_config = None

    def init_user_db(self, user_params):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session
        from sqlalchemy.orm import sessionmaker

        postgres_uri = self.config.get(user_params.get('postgres_uri')) \
            or user_params.get('postgres_uri')

        print(postgres_uri)
        if postgres_uri:
            engine = create_engine(postgres_uri)
            self.db_session = scoped_session(sessionmaker(autoflush=False, bind=engine))
        else:
            raise Exception('Could not init user db')

        # TODO: check for False status, log error
        self.user_api_config = MongoUserApiConfigLoader(self.mongo.db, user_params).get_user_api_config()

    def exec_safe_session(self, service_func=None, *args):
        if service_func:
            try:
                service_func(*args)
            except Exception as exc:
                if self.db_session is not None:
                    self.db_session.rollback()
                raise type(exc)('Data Push Error: {0}: {1}'.format(type(exc).__name__, exc.args))
            finally:
                if self.db_session is not None:
                    self.db_session.remove()

    def sync_data_to_mc(self, table):
        if table not in self._models.keys():
            self.logger.error('error, selected table is not available for mc sync')

        dp = DataPusher(self.config,
                        self.logger,
                        self.db_session,
                        self._models[table],
                        self.mongo,
                        self.user_api_config[1])

        resp = dp.sync_table()
        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        # No operation performed is not a real error when there're no records to update/insert
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))

    def clean_sync_flags(self, table):
        if table not in self._models.keys():
            self.logger.warning('error, selected table is not available for this operation')

        try:
            model = self._models[table]
            for rec in self.db_session.query(model):
                rec._last_ext_sync = None
                self.db_session.add(rec)
            self.db_session.commit()
            self.logger.info('successfully cleared ext sync flags on all records')
        except:
            self.logger.warning('failure in resetting ext_sync_flags')

    # TODO: Add another func to take query object

    def sync_query_to_mc(self, query_rules):
        dp = DataPusher(self.config,
                        self.logger,
                        self.db_session,
                        self._models['customer'],
                        self.mongo,
                        self.user_api_config[1])
        resp = dp.sync_query(name=query_rules['name'],
                             query=SqlQueryConstructor(self.db_session, query_rules,
                                                       customer_only=True).construct_sql_query())

        if resp and hasattr(resp, 'code'):
            self.logger.info('sync result:' + str(resp.code))
        else:
            self.logger.error('error with sync, see logs')
            self.logger.error(str(resp))

import copy
import os
import requests
import sys
import traceback
import yaml

from .classes.api_data import ApiData, ApiDataToSql, ApiDataToMongo
from .classes.ftp_file import ZipFile, CsvFile
from .mongo_user_config_loader import MongoUserApiConfigLoader
from ...common.services import DbService
from ...common.models.user_models import StgEmlSend, EmlSend, StgEmlOpen, EmlOpen, StgEmlClick, EmlClick, StgSendJob, \
    SendJob, Customer, Purchase, WebTrackingEvent, WebTrackingPageView, WebTrackingEcomm

# user specific: authentication + domain
"""
user_api_config = {
    'magento':  {'domain': "http://127.0.0.1:32768",# domain address before 'index.php'
                 'token': "npk3nc7gyhn8leab9baifl5075q45uhl"
                 },

    'x2crm':    {'domain': "http://demo.x2crm.com",
                 'token': "YWRtaW46dGVzdA=="
                 },

    'shopify':  {'domain': "https://@xspeed.myshopify.com",
                 'id': '20627b91731e8d8ee338bf786ae29feb',
                 'secret': '045febd59c1d2acc3d00ac309360ea46'
                 },

    'bigcommerce':  {'domain': "https://store-vd63texh7u.mybigcommerce.com",
                     'id': 'test',
                     'secret': '07d63370ed9ddb2eee9143acb91b18af38cb5b9d'
                     },

    'stripe':   {'domain': "https://api.stripe.com/v1",
                 'id': 'sk_test_C9SgTuKd9DN2PT6hFLPMzlts',
                 'secret': ''
                 }
}
"""

# general config based on data_source
"""
api_config = {
    'magento': {
        'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '
        },
        'params': None,
        'customer': {
            'endpoint': "/index.php/rest/V1/customers/search?searchCriteria",
            'primary_keys': ['customer_id'],
            'json_data_keys': 'items',
            'db_field_map': dict(customer_id='id',
                                 email_address='email',
                                 fname='firstname',
                                 lname='lastname',
                                 created_at='created_at',
                                 # marketing_allowed='accepts_marketing',
                                 # purchase_count='orders_count',
                                 # total_spent_so_far='total_spent'
                                 )
        },
        'purchase': {
            'endpoint': "/index.php/rest/V1/orders?searchCriteria",
            'primary_keys': ['purchase_id'],
            'json_data_keys': 'items',
            'db_field_map': dict(purchase_id='quote_id',
                                 customer_id='customer_id',
                                 created_at='created_at',
                                 price='total_invoiced',
                                 # is_paid='financial_status',
                                 # referring_site='referring_site',
                                 # landing_site='landing_site',
                                 # browser_ip='browser_ip',
                                 # user_agent='client_details.user_agent'
                                 )
        }
    },

    'x2crm': {
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Basic '
        },
        'params': None,
        'customer': {
            'endpoint': "/index.php/api2/Contacts/",
            'primary_keys': ['customer_id'],
            'json_data_keys': None,

            'db_field_map': dict(customer_id='id',
                                 email_address='email',
                                 fname='firstName',
                                 city='city',
                                 interest_area='interest',
                                 lname='lastName',
                                 created_at='createDate',
                                 # marketing_allowed='accepts_marketing',
                                 # purchase_count='orders_count',
                                 # total_spent_so_far='total_spent'
                                 )
        }
    },

    'shopify': {
        'headers': {'Content-Type': 'application/json'},
        'params': None,
        'purchase': {
            # os.getenv('SHOPIFY_PURCHASE_API_ENDPOINT'),
            'endpoint': "/admin/orders.json",
            'primary_keys': ['purchase_id'],
            'json_data_keys': 'orders',
            'db_field_map': dict(purchase_id='id',
                                 customer_id='customer.id',
                                 created_at='created_at',
                                 price='total_price',
                                 is_paid='financial_status',
                                 referring_site='referring_site',
                                 landing_site='landing_site',
                                 browser_ip='browser_ip',
                                 user_agent='client_details.user_agent')
        },
        'customer': {
            'endpoint': "/admin/customers.json",
            'primary_keys': ['customer_id'],
            'json_data_keys': 'customers',
            'db_field_map': dict(customer_id='id',
                                 email_address='email',
                                 fname='first_name',
                                 lname='last_name',
                                 marketing_allowed='accepts_marketing',
                                 created_at='created_at',
                                 purchase_count='orders_count',
                                 total_spent_so_far='total_spent')
        }
    },
    'bigcommerce': {
        'headers': {'Content-Type': 'application/json'},
        'params': None,
        'purchase': {
            'endpoint': "/api/v2/orders.json",
            'primary_keys': ['purchase_id'],
            'json_data_keys': None,
            'db_field_map': dict(purchase_id='id',
                                 customer_id='customer_id',
                                 created_at='date_created',
                                 price='total_ex_tax',
                                 is_paid='payment_status',
                                 browser_ip='ip_address')
        },
        'customer': {
            'endpoint': "/api/v2/customers.json",
            'primary_keys': ['customer_id'],
            'json_data_keys': None,
            'db_field_map': dict(customer_id='id',
                                 email_address='email',
                                 fname='first_name',
                                 lname='last_name',
                                 marketing_allowed='accepts_marketing',
                                 created_at='date_created')
                                 # purchase_count='orders_count',
                                 # total_spent_so_far='total_spent')
        }
    },
    'stripe': {
        'headers': {'Content-Type': 'application/json'},
        'params': None,
        'customer': {
            'endpoint': "/customers",
            'primary_keys': ['customer_id'],
            'json_data_keys': 'data',
            'db_field_map': dict(customer_id='id',
                                 email_address='email',
                                 # fname='first_name',
                                 # lname='last_name',
                                 # marketing_allowed='accepts_marketing',
                                 created_at='created')
            # purchase_count='orders_count',
            # total_spent_so_far='total_spent')
        }
    }
}
"""


class DataLoadService(DbService):
    def __init__(self, config, logger, db, db_session, mongo):
        super(DataLoadService, self).__init__(config, db, logger)
        self.db_session = db_session
        self.mongo = mongo
        self.data_type_map = {'customer': Customer,
                              'purchase': Purchase
                              }
        self.api_config_file = 'api_config.yml'
        self.data_load_config = self.load_config()
        self.user_api_config = MongoUserApiConfigLoader(self.mongo.db).get_user_api_config()

    def load_config(self):
        try:
            with open(self.api_config_file) as config_file:
                return yaml.load(config_file)
        except Exception:
            return {}

    def exec_safe_session(self, load_func=None, *args, **kwargs):
        if load_func:
            try:
                load_func(*args, **kwargs)
            except Exception as exc:
                if self.db_session is not None:
                    self.db_session.rollback()
                raise type(exc)('DataLoad Error: {0}: {1}'.format(type(exc).__name__, exc.args))
            finally:
                if self.db_session is not None:
                    self.db_session.remove()

    def get_api_args(self, data_source, data_type):
        vendor_config = self.data_load_config.get(data_source, {})
        api_args = copy.copy(vendor_config.get(data_type, {}))

        user_config = None

        # TODO: check for False status, log error
        status, vendor_configs = self.user_api_config
        if status is True:
            for vendor_user_config in vendor_configs:
                if vendor_user_config.get('data_source') == data_source:
                    user_config = vendor_user_config
                    break
        else:
            raise Exception(vendor_configs)

        if not vendor_configs or not user_config:
            raise Exception('Vendor {0} is not supported'.format(data_source))

        api_args['headers'] = copy.copy(vendor_config.get('headers'))
        if 'token' in user_config.keys():
            api_args['headers']['Authorization'] += user_config['token']
        elif 'id' in user_config.keys():
            api_args['auth'] = (user_config['id'], user_config['secret'])

        if 'endpoint' in api_args:
            api_args['endpoint'] = user_config['domain'] + api_args['endpoint']
        elif 'pagination' in api_args:
            for a_key in api_args['pagination'].keys():
                if a_key.endswith('endpoint') and not api_args['pagination'][a_key].startswith('http'):
                    api_args['pagination'][a_key] = user_config['domain'] + api_args['pagination'][a_key]

        api_args['params'] = vendor_config.get('params')
        api_args['transform_response_data'] = vendor_config.get('transform_response_data')
        api_args['db_model'] = self.data_type_map.get(data_type)
        api_args['db_session'] = self.db_session

        return api_args

    def simple_data_load(self, **kwargs):
        api_call_config = self.get_api_args(kwargs['data_source'], kwargs['data_type'])
        if api_call_config is not None:
            ad1 = ApiDataToSql(**api_call_config)
            ad1.load_data()

    def load_lead_perfection(self):
        config = self.config
        mc_data_creds = config.get('EXT_DATA_CREDS').get(config.get('CUSTOMER_DATA_SOURCE'))
        cfg = {
            'host': mc_data_creds.get('ftp_url'),
            'username': mc_data_creds.get('ftp_user'),
            'password': mc_data_creds.get('ftp_pass')
        }
        filename = mc_data_creds.get('filename')
        filepath = mc_data_creds.get('filepath')
        csv = CsvFile(file=filename,
                      db_session=self.db_session,
                      db_model=Customer,
                      primary_keys=['customer_id'],
                      db_field_map=dict(
                          customer_id='SubscriberKey',
                          email_address='EmailAddress',
                          fname='firstname',
                          lname='lastname',
                          created_at='EntryDate',
                          city='City',
                          state='State',
                          interest_area='Productid',
                          status='ds_id',
                          source='src_id',
                          sales_rep='SalesRepName',
                          last_communication='LastCall'
                      ),
                      ftp_path=filepath,
                      ftp_cfg=cfg,
                      file_encoding='utf16')

        # load lead perfection data to db
        csv.load_data()

    def load_mc_email_data(self):
        config = self.config
        mc_data_creds = config.get('EXT_DATA_CREDS').get(config.get('EMAIL_DATA_SOURCE'))
        cfg = {
            'host': mc_data_creds.get('ftp_url'),
            'username': mc_data_creds.get('ftp_user'),
            'password': mc_data_creds.get('ftp_pass')
        }
        filename = mc_data_creds.get('filename')
        filepath = mc_data_creds.get('filepath')
        zf = ZipFile(file=filename,
                     ftp_path=filepath,
                     ftp_cfg=cfg)

        engine_instance = self.db_session.get_bind()

        try:
            # load Sendjobs data to db
            zf.load_data(file='SendJobs.csv',
                         db_session=self.db_session,
                         db_model=StgSendJob,
                         primary_keys=['SendID'],
                         db_field_map={
                             'SendID': 'SendID',
                             'SendDefinitionExternalKey': 'SendDefinitionExternalKey',
                             'EmailName': 'EmailName',
                             'SchedTime': 'SchedTime',
                             'SentTime': 'SentTime',
                             'Subject': 'Subject',
                             'PreviewURL': 'PreviewURL'
                         })

            sql = 'INSERT INTO send_job("SendID", "SendDefinitionExternalKey", "EmailName", "SchedTime", "SentTime", "Subject", "PreviewURL") ' \
                  'SELECT DISTINCT ON (a."SendID") a."SendID", a."SendDefinitionExternalKey", a."EmailName", a."SchedTime", a."SentTime", a."Subject", a."PreviewURL" ' \
                  'FROM stg_send_job a ' \
                  'LEFT JOIN send_job b ' \
                  'ON b."SendID" = a."SendID" ' \
                  'WHERE b."SendID" IS NULL '
            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' sendjobs')

            sql = 'DELETE FROM stg_send_job'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing SendJobs.csv' + traceback.print_tb(exc_traceback))
        try:
            zf.load_data(file='Sent.csv',
                         db_session=self.db_session,
                         db_model=StgEmlSend,
                         primary_keys=['SubscriberKey', 'EventDate'],
                         db_field_map={
                             'SendID': 'SendID',
                             'SubscriberKey': 'SubscriberKey',
                             'EmailAddress': 'EmailAddress',
                             'EventDate': 'EventDate'
                         })

            sql = 'INSERT INTO eml_send ("SendID", "SubscriberKey", "EmailAddress", "EventDate") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", a."EmailAddress", a."EventDate" ' \
                  'FROM stg_eml_send a ' \
                  'LEFT JOIN eml_send b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '

            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' sends')

            sql = 'DELETE FROM stg_eml_send'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Sent.csv' + traceback.print_tb(exc_traceback))
        try:
            # load Opens data to db
            zf.load_data(file='Opens.csv',
                         db_session=self.db_session,
                         db_model=StgEmlOpen,
                         primary_keys=['SubscriberKey', 'EventDate'],
                         db_field_map={
                             'SendID': 'SendID',
                             'SubscriberKey': 'SubscriberKey',
                             'EmailAddress': 'EmailAddress',
                             'EventDate': 'EventDate',
                             'IsUnique': 'IsUnique',
                             'IpAddress': 'IpAddress',
                             'Country': 'Country',
                             'Region': 'Region',
                             'City': 'City',
                             'Latitude': 'Latitude',
                             'Longitude': 'Longitude',
                             'MetroCode': 'MetroCode',
                             'AreaCode': 'AreaCode',
                             'Browser': 'Browser',
                             'EmailClient': 'EmailClient',
                             'OperatingSystem': 'OperatingSystem',
                             'Device': 'Device'
                         })

            sql = 'INSERT INTO eml_open("SendID", "SubscriberKey", "EmailAddress", "EventDate", "IsUnique", "IpAddress", "Country", "Region", "City", "Latitude", "Longitude", "MetroCode", "AreaCode", "Browser", "EmailClient", "OperatingSystem", "Device") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", a."EmailAddress", a."EventDate", a."IsUnique", a."IpAddress", a."Country", a."Region", a."City", a."Latitude", a."Longitude", a."MetroCode", a."AreaCode", a."Browser", a."EmailClient", a."OperatingSystem", a."Device" ' \
                  'FROM stg_eml_open a ' \
                  'LEFT JOIN eml_open b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '

            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' opens')

            sql = 'DELETE FROM stg_eml_open'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Opens.csv' + traceback.print_tb(exc_traceback))
        try:
            # load Clicks data to db
            zf.load_data(file='Clicks.csv',
                         db_session=self.db_session,
                         db_model=StgEmlClick,
                         primary_keys=['SubscriberKey', 'EventDate'],
                         db_field_map={
                             'SendID': 'SendID',
                             'SubscriberKey': 'SubscriberKey',
                             'EmailAddress': 'EmailAddress',
                             'EventDate': 'EventDate',
                             'SendURLID': 'SendURLID',
                             'URLID': 'URLID',
                             'URL': 'URL',
                             'Alias': 'Alias',
                             'IsUnique': 'IsUnique',
                             'IpAddress': 'IpAddress',
                             'Country': 'Country',
                             'Region': 'Region',
                             'City': 'City',
                             'Latitude': 'Latitude',
                             'Longitude': 'Longitude',
                             'MetroCode': 'MetroCode',
                             'AreaCode': 'AreaCode',
                             'Browser': 'Browser',
                             'EmailClient': 'EmailClient',
                             'OperatingSystem': 'OperatingSystem',
                             'Device': 'Device'
                         })

            sql = 'INSERT INTO eml_click("SendID", "SubscriberKey", "EmailAddress", "EventDate", "URLID", "URL", "Alias", "IsUnique", "IpAddress", "Country", "Region", "City", "Latitude", "Longitude", "MetroCode", "AreaCode", "Browser", "EmailClient", "OperatingSystem", "Device") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", a."EmailAddress", a."EventDate", a."URLID", a."URL", a."Alias", a."IsUnique", a."IpAddress", a."Country", a."Region", a."City", a."Latitude", a."Longitude", a."MetroCode", a."AreaCode", a."Browser", a."EmailClient", a."OperatingSystem", a."Device" ' \
                  'FROM stg_eml_click a ' \
                  'LEFT JOIN eml_click b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '

            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' clicks')

            sql = 'DELETE FROM stg_eml_click'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Clicks.csv' + traceback.print_tb(exc_traceback))

        zf.clean_up()  # delete downloaded files

        try:
            # execute separate load of exported Journey-based sends information
            filename = 'journey_sends.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db_session,
                          db_model=StgEmlSend,
                          primary_keys=['SubscriberKey', 'EventDate'],
                          db_field_map={
                              'SendID': 'SendID',
                              'SubscriberKey': 'SubscriberKey',
                              'TriggeredSendExternalKey': 'TriggererSendDefinitionObjectID',
                              'EventDate': 'EventDate'
                          },
                          ftp_path=filepath,
                          ftp_cfg=cfg,
                          file_encoding='utf16')

            # load journey send data to db
            csv.load_data()

            sql = 'INSERT INTO eml_send ("SendID", "SubscriberKey", "EventDate", "TriggeredSendExternalKey") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", a."EventDate", a."TriggeredSendExternalKey" ' \
                  'FROM stg_eml_send a ' \
                  'LEFT JOIN eml_send b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '

            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' sends')

            sql = 'UPDATE eml_send ' \
                  'SET "TriggeredSendExternalKey" = ' \
                  '(SELECT "TriggeredSendExternalKey" ' \
                  'FROM stg_eml_send a ' \
                  'WHERE a."SubscriberKey" = eml_send."SubscriberKey" ' \
                  'AND a."EventDate" = eml_send."EventDate")'
            res = engine_instance.execute(sql)
            print('updated ' + str(res.rowcount) + ' sends')

            sql = 'DELETE FROM stg_eml_send'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_sends.csv' + traceback.print_tb(exc_traceback))
        try:
            # execute separate load of exported Journey-based opens information
            filename = 'journey_opens.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db_session,
                          db_model=StgEmlOpen,
                          primary_keys=['SubscriberKey', 'EventDate'],
                          db_field_map={
                              'SendID': 'SendID',
                              'SubscriberKey': 'SubscriberKey',
                              'TriggeredSendExternalKey': 'TriggererSendDefinitionObjectID',
                              'EventDate': 'EventDate'
                          },
                          ftp_path=filepath,
                          ftp_cfg=cfg,
                          file_encoding='utf16')

            # load journey opens data to db
            csv.load_data()

            sql = 'INSERT INTO eml_open("SendID", "SubscriberKey", "EventDate", "TriggeredSendExternalKey") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", a."EventDate", a."TriggeredSendExternalKey" ' \
                  'FROM stg_eml_open a ' \
                  'LEFT JOIN eml_open b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '

            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' opens')

            sql = 'UPDATE eml_open ' \
                  'SET "TriggeredSendExternalKey" = ' \
                  '(SELECT "TriggeredSendExternalKey" ' \
                  'FROM stg_eml_open a ' \
                  'WHERE a."SubscriberKey" = eml_open."SubscriberKey" ' \
                  'AND a."EventDate" = eml_open."EventDate")'
            res = engine_instance.execute(sql)
            print('updated ' + str(res.rowcount) + ' opens')

            sql = 'DELETE FROM stg_eml_open'
            engine_instance.execute(sql)

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_opens.csv' + traceback.print_tb(exc_traceback))
        try:
            # execute separate load of exported Journey-based clicks information
            filename = 'journey_clicks.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db_session,
                          db_model=StgEmlClick,
                          primary_keys=['SubscriberKey', 'EventDate'],
                          db_field_map={
                              'SendID': 'SendID',
                              'SubscriberKey': 'SubscriberKey',
                              'TriggeredSendExternalKey': 'TriggererSendDefinitionObjectID',
                              'EventDate': 'EventDate'
                          },
                          ftp_path=filepath,
                          ftp_cfg=cfg,
                          file_encoding='utf16')

            # load journey click data to db
            csv.load_data()

            sql = 'INSERT INTO eml_click("SendID", "SubscriberKey", "EventDate", "TriggeredSendExternalKey") ' \
                  'SELECT DISTINCT ON (a."SubscriberKey", a."EventDate") a."SendID", a."SubscriberKey", ' \
                  'a."EventDate", a."TriggeredSendExternalKey" ' \
                  'FROM stg_eml_click a ' \
                  'LEFT JOIN eml_click b ' \
                  'ON b."SubscriberKey" = a."SubscriberKey" ' \
                  'AND b."EventDate" = a."EventDate" ' \
                  'WHERE b."SubscriberKey" IS NULL '
            res = engine_instance.execute(sql)
            print('inserted ' + str(res.rowcount) + ' clicks')

            sql = 'UPDATE eml_click ' \
                  'SET "TriggeredSendExternalKey" = ' \
                  '(SELECT "TriggeredSendExternalKey" ' \
                  'FROM stg_eml_click a ' \
                  'WHERE a."SubscriberKey" = eml_click."SubscriberKey" ' \
                  'AND a."EventDate" = eml_click."EventDate")'
            engine_instance.execute(sql)

            sql = 'DELETE FROM stg_eml_click'
            res = engine_instance.execute(sql)
            print('updated ' + str(res.rowcount) + ' clicks')

        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_clicks.csv' + str(exc) + traceback.print_tb(exc_traceback))

        # TODO: append county FIPS codes to open and click data

        # append sent/open/click counts to SendJob rows
        sends = self.db_session.query(SendJob).all()
        for send in sends:
            send._get_stats()

    def load_mc_journeys(self):
        token = self.__get_mc_auth()
        print('load_mc_journeys: token: ', token)
        journeys = self.__get_mc_journeys(token)
        self.__load_mc_journeys_to_mongo(journeys, token)

    def __get_mc_auth(self):
        # TODO: resolve duplicated code in emails/services/classes/esp_push.py for images
        config = self.config
        mc_data_creds = config.get('EXT_DATA_CREDS').get(config.get('EMAIL_DATA_DEST'))
        # get auth token
        url = mc_data_creds.get('auth_url')  # was 'https://auth.exacttargetapis.com/v1/requestToken'
        body = dict(clientId=mc_data_creds.get('id'),  # was '3t1ch44ej7pb4p117oyr7m4g',
                    clientSecret=mc_data_creds.get('secret'))  # was '2Cegvz6Oe9qTmc8HMUn2RWKh')
        r = requests.post(url, data=body)
        if r.status_code != 200:
            raise PermissionError('ET auth code retrieval: failed to get auth token')
        token = r.json().get('accessToken', None)
        if not token:
            raise ValueError('error, no accessToken value returned')
        return token

    def __get_mc_journeys(self, token):

        ad = ApiData(endpoint='https://www.exacttargetapis.com/interaction/v1/interactions',
                     auth=None,
                     headers={'Content-Type': 'application/json',
                              'Authorization': 'Bearer ' + token},
                     params=None)
        journeys = ad.get_data().json()
        return journeys

    def __load_mc_journeys_to_mongo(self, journeys, token):

        if self.user_params is not None:
            collection = self.mongo.db['journeys_' + self.user_params.get('account_name', '')]
        else:
            collection = self.mongo.db.journeys

        for journey in journeys['items']:
            try:
                adm = ApiDataToMongo(
                    endpoint='https://www.exacttargetapis.com/interaction/v1/interactions/' + journey['id'],
                    auth=None,
                    headers={'Content-Type': 'application/json',
                             'Authorization': 'Bearer ' + token},
                    params=None,
                    collection=collection,
                    primary_keys=['id'])
                adm.load_data()
            except KeyError as exc:
                print('problem with journey id [' + journey['id'] + ']')

    def load_web_tracking(self, startDate=None, endDate=None):

        if startDate is None:
            startDate = '1daysAgo'
        if endDate is None:
            endDate = 'today'

        from apiclient.discovery import build
        from oauth2client.service_account import ServiceAccountCredentials
        import httplib2

        SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
        DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
        KEY_FILE_LOCATION = 'bluenilesw-app-f937c2e51267.p12'
        SERVICE_ACCOUNT_EMAIL = 'bluenile-sw-google-analytics@bluenilesw-app.iam.gserviceaccount.com'
        VIEW_ID = '122242971'

        credentials = ServiceAccountCredentials.from_p12_keyfile(
            SERVICE_ACCOUNT_EMAIL, KEY_FILE_LOCATION, scopes=SCOPES)

        http = credentials.authorize(httplib2.Http())

        # Build the service object.
        analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

        def load_web_tracking_data(model, dims, metrics, db_field_map):
            response = analytics.reports().batchGet(
                body={
                    'reportRequests': [
                        {
                            'viewId': VIEW_ID,
                            'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
                            'metrics': [
                                {'expression': metrics[0]},
                                {'expression': metrics[1]},
                                {'expression': metrics[2]}
                            ],
                            'dimensions': [
                                {'name': 'ga:dimension1'},
                                {'name': 'ga:dimension3'},
                                {'name': 'ga:dimension2'},
                                {'name': dims[0]},
                                {'name': dims[1]},
                                {'name': dims[2]},
                                {'name': dims[3]}
                            ]
                        }]
                }
            ).execute()

            ad = ApiDataToSql(db_session=self.db_session,
                              db_model=model,
                              primary_keys=['browser_id', 'utc_millisecs'],
                              db_field_map=db_field_map,
                              json_data_keys='reports[0].data.rows')

            ad.load_data(preload_data=response)

        try:
            load_web_tracking_data(WebTrackingPageView,
                                   dims=('ga:pagePath', 'ga:browser', 'ga:browserSize', 'ga:operatingSystem'),
                                   metrics=('ga:sessions', 'ga:pageValue', 'ga:pageviews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     page_path='dimensions[3]',
                                                     browser='dimensions[4]',
                                                     browser_size='dimensions[5]',
                                                     operating_system='dimensions[6]',
                                                     sessions='metrics[0].values[0]',
                                                     page_value='metrics[0].values[1]',
                                                     page_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingPageView,
                                   dims=('ga:pagePath', 'ga:deviceCategory', 'ga:mobileDeviceBranding',
                                         'ga:mobileDeviceModel'),
                                   metrics=('ga:sessions', 'ga:pageValue', 'ga:pageviews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     page_path='dimensions[3]',
                                                     device_category='dimensions[4]',
                                                     mobile_device_branding='dimensions[5]',
                                                     mobile_device_model='dimensions[6]',
                                                     sessions='metrics[0].values[0]',
                                                     page_value='metrics[0].values[1]',
                                                     page_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingPageView,
                                   dims=('ga:pagePath', 'ga:country', 'ga:region', 'ga:metro'),
                                   metrics=('ga:sessions', 'ga:pageValue', 'ga:pageviews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     page_path='dimensions[3]',
                                                     country='dimensions[4]',
                                                     region='dimensions[5]',
                                                     metro='dimensions[6]',
                                                     sessions='metrics[0].values[0]',
                                                     page_value='metrics[0].values[1]',
                                                     page_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingPageView,
                                   dims=('ga:pagePath', 'ga:city', 'ga:latitude', 'ga:longitude'),
                                   metrics=('ga:sessions', 'ga:pageValue', 'ga:pageviews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     page_path='dimensions[3]',
                                                     city='dimensions[4]',
                                                     latitude='dimensions[5]',
                                                     longitude='dimensions[6]',
                                                     sessions='metrics[0].values[0]',
                                                     page_value='metrics[0].values[1]',
                                                     page_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:eventLabel', 'ga:eventCategory', 'ga:browser'),
                                   metrics=('ga:eventValue', 'ga:sessionsWithEvent', 'ga:totalEvents'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     event_action='dimensions[3]',
                                                     event_label='dimensions[4]',
                                                     event_category='dimensions[5]',
                                                     browser='dimensions[6]',
                                                     event_value='metrics[0].values[0]',
                                                     sessions_with_event='metrics[0].values[1]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:browser', 'ga:browserSize', 'ga:operatingSystem'),
                                   metrics=('ga:eventValue', 'ga:sessionsWithEvent', 'ga:totalEvents'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     event_action='dimensions[3]',
                                                     browser='dimensions[4]',
                                                     browser_size='dimensions[5]',
                                                     operating_system='dimensions[6]',
                                                     event_value='metrics[0].values[0]',
                                                     sessions_with_event='metrics[0].values[1]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:deviceCategory', 'ga:mobileDeviceBranding',
                                         'ga:mobileDeviceModel'),
                                   metrics=('ga:eventValue', 'ga:sessionsWithEvent', 'ga:totalEvents'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     event_action='dimensions[3]',
                                                     device_category='dimensions[4]',
                                                     mobile_device_branding='dimensions[5]',
                                                     mobile_device_model='dimensions[6]',
                                                     event_value='metrics[0].values[0]',
                                                     sessions_with_event='metrics[0].values[1]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:country', 'ga:region', 'ga:metro'),
                                   metrics=('ga:eventValue', 'ga:sessionsWithEvent', 'ga:totalEvents'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     event_action='dimensions[3]',
                                                     country='dimensions[4]',
                                                     region='dimensions[5]',
                                                     metro='dimensions[6]',
                                                     event_value='metrics[0].values[0]',
                                                     sessions_with_event='metrics[0].values[1]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:city', 'ga:latitude', 'ga:longitude'),
                                   metrics=('ga:eventValue', 'ga:sessionsWithEvent', 'ga:totalEvents'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     event_action='dimensions[3]',
                                                     city='dimensions[4]',
                                                     latitude='dimensions[5]',
                                                     longitude='dimensions[6]',
                                                     event_value='metrics[0].values[0]',
                                                     sessions_with_event='metrics[0].values[1]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEcomm,
                                   dims=('ga:browser', 'ga:browserSize', 'ga:operatingSystem', 'ga:deviceCategory'),
                                   metrics=('ga:totalValue', 'ga:itemQuantity', 'ga:productDetailViews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     browser='dimensions[3]',
                                                     browser_size='dimensions[4]',
                                                     operating_system='dimensions[5]',
                                                     device_category='dimensions[6]',
                                                     total_value='metrics[0].values[0]',
                                                     item_quantity='metrics[0].values[1]',
                                                     product_detail_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEcomm,
                                   dims=('ga:mobileDeviceBranding', 'ga:mobileDeviceModel', 'ga:country', 'ga:region'),
                                   metrics=('ga:totalValue', 'ga:itemQuantity', 'ga:productDetailViews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     mobile_device_branding='dimensions[3]',
                                                     mobile_device_model='dimensions[4]',
                                                     country='dimensions[5]',
                                                     region='dimensions[6]',
                                                     total_value='metrics[0].values[0]',
                                                     item_quantity='metrics[0].values[1]',
                                                     product_detail_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))
        try:
            load_web_tracking_data(WebTrackingEcomm,
                                   dims=('ga:metro', 'ga:city', 'ga:latitude', 'ga:longitude'),
                                   metrics=('ga:totalValue', 'ga:itemQuantity', 'ga:productDetailViews'),
                                   db_field_map=dict(browser_id='dimensions[0]',
                                                     utc_millisecs='dimensions[2]',
                                                     hashed_email='dimensions[1]',
                                                     metro='dimensions[3]',
                                                     city='dimensions[4]',
                                                     latitude='dimensions[5]',
                                                     longitude='dimensions[6]',
                                                     total_value='metrics[0].values[0]',
                                                     item_quantity='metrics[0].values[1]',
                                                     product_detail_views='metrics[0].values[2]'))
            print('successfully loaded part of web tracking data')
        except Exception as exc:
            print('failed one of the web tracking lookups: ' + str(exc))

    # this works with the fips_codes_website.csv file - which has the right FIPS values to match
    # - up with the ids of the us-10m.v1.json data from D3
    def add_fips_location_data(self, table, city_field=None, state_field=None, dest_fips_code_field=None):

        # how it works: it goes one by one through each FIPS code in the csv file
        # - and for each, searches the table for any records with that state/city
        # - and if it finds some, it throws the FIPS code on the field specified and saves back the records
        # - then moves on to the next


        filename = 'static/data/fips_codes_website.csv'
        db_session = self.db_session
        if city_field is None:
            city_field = 'City'
        if state_field is None:
            state_field = 'Region'
        if dest_fips_code_field is None:
            fips_field = 'AreaCode'

        table_map = {'EmlOpen': EmlOpen,
                     'EmlClick': EmlClick}
        model = table_map.get(table, None)
        if table is None:
            return Exception('table not recognized or authorized to apply fips location code data to.')

        city = getattr(model, city_field)
        state = getattr(model, state_field)

        import csv
        with open(filename, 'r') as csvfile:
            csvfile_reader = csv.DictReader(csvfile, delimiter=',')
            already_processed = []

            # using city names without spaces
            for row in csvfile_reader:

                if (row['GU Name'], row['State Abbreviation']) in already_processed:
                    continue

                already_processed.append((row['GU Name'], row['State Abbreviation']))

                recs = db_session.query(model).filter(city == row['GU Name'].replace(' ', '').upper(),
                                          state == row['State Abbreviation']).all()
                # print('*', end='', flush=True)
                if len(recs) > 0:
                    print('found ' + str(len(recs)) + ' records with city ' + row['GU Name'].replace(' ', ''))
                    for rec in recs:
                        rec.__setattr__(fips_field, str(row['State FIPS Code'] + row['County FIPS Code']))
                        db_session.add(rec)
                    db_session.commit()


class UserDataLoadService(DataLoadService):
    def __init__(self, config, logger, mongo):
        self.config = config
        self.logger = logger
        self.mongo = mongo
        self.db_session = None
        self.user_params = None
        self.data_type_map = {'customer': Customer,
                              'purchase': Purchase
                              }
        self.api_config_file = 'api_config.yml'
        self.data_load_config = self.load_config()

    def init_user_db(self, user_params, postgres=True):
        self.user_params = user_params

        postgres_uri = self.user_params.get('postgres_uri')
        if postgres_uri and postgres is True:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import scoped_session
            from sqlalchemy.orm import sessionmaker

            engine = create_engine(postgres_uri)
            self.db_session = scoped_session(sessionmaker(bind=engine))

        self.user_api_config = MongoUserApiConfigLoader(self.mongo.db, user_params).get_user_api_config()

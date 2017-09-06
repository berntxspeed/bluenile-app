import copy
import os
import requests
import sys
import traceback
import yaml

from .classes.api_data import ApiData, ApiDataToSql, ApiDataToMongo
from .classes.ftp_file import ZipFile, CsvFile
from .mongo_user_config_loader import MongoUserApiConfigLoader
from ...common.models.user_models import StgEmlSend, EmlSend, StgEmlOpen, EmlOpen, StgEmlClick, EmlClick, StgSendJob, \
    SendJob, Customer, Purchase, WebTrackingEvent, WebTrackingPageView, WebTrackingEcomm


class UserDataLoadService:
    def __init__(self, config, logger, mongo):
        self.config = config
        self.logger = logger
        self.mongo = mongo
        self.db_session = None
        self.user_params = None
        self.data_type_map = {'customer': Customer,
                              'purchase': Purchase,
                              'stg_eml_send': StgEmlSend,
                              'stg_eml_click': StgEmlClick,
                              'stg_eml_open': StgEmlOpen,
                              'stg_send_job': StgSendJob
                              }
        self.api_config_file = os.path.abspath(os.path.join(self.config['CONFIG_FOLDER'], 'api_config.yml'))
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

    def get_mc_creds(self, data_source):
        vendor_config = self.data_load_config.get(data_source, {}).get('creds', {})
        mc_api_args = copy.copy(vendor_config)

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
            raise Exception(f'Vendor {data_source} is not supported')

        for a_key in user_config.keys():
            mc_api_args[a_key] = user_config[a_key]

        return mc_api_args

    def simple_data_load(self, **kwargs):
        api_call_config = self.get_api_args(kwargs['data_source'], kwargs['data_type'])
        if api_call_config is not None:
            ad1 = ApiDataToSql(**api_call_config)
            ad1.load_data()
    """
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
    """

    def get_mc_data_load_args(self, filename, data_source, data_type, cfg=None):
        file_config = self.data_load_config[data_source]['file_map'].get(filename, {})
        data_load_config = copy.copy(file_config)

        if not data_load_config:
            raise Exception(f'File {filename} is not a valid source of data')

        data_load_config['file'] = filename
        data_load_config['db_model'] = self.data_type_map.get(data_type)
        data_load_config['db_session'] = self.db_session
        if cfg is not None:
            data_load_config['ftp_cfg'] = cfg

        return data_load_config

    def load_mc_email_data(self, **kwargs):
        mc_data_config_args = self.get_mc_creds(kwargs['data_source'])
        cfg = {
            'host': mc_data_config_args.get('ftp_url'),
            'username': mc_data_config_args.get('id'),
            'password': mc_data_config_args.get('secret')
        }
        filename = mc_data_config_args.get('filename')
        filepath = mc_data_config_args.get('filepath')
        zf = ZipFile(file=filename,
                     ftp_path=filepath,
                     ftp_cfg=cfg)

        engine_instance = self.db_session.get_bind()

        try:
            # load Sendjobs data to db
            zf_args = self.get_mc_data_load_args('SendJobs.csv', 'mc_email_data', 'stg_send_job')
            # execute separate load of exported Journey-based clicks information
            zf.load_data(**zf_args)
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
            zf_args = self.get_mc_data_load_args('Sent.csv', 'mc_email_data', 'stg_eml_send')
            zf.load_data(**zf_args)
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
            zf_args = self.get_mc_data_load_args('Opens.csv', 'mc_email_data', 'stg_eml_open')
            zf.load_data(**zf_args)

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
            zf_args = self.get_mc_data_load_args('Opens.csv', 'mc_email_data', 'stg_eml_open')
            # load Clicks data to db
            zf.load_data(**zf_args)

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
            csv_args = self.get_mc_data_load_args('journey_sends.csv', 'mc_email_data', 'stg_eml_send', cfg)
            # execute separate load of exported Journey-based sends information
            csv = CsvFile(**csv_args)
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
            csv_args = self.get_mc_data_load_args('journey_opens.csv', 'mc_email_data', 'stg_eml_open', cfg)
            csv = CsvFile(**csv_args)
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
            csv_args = self.get_mc_data_load_args('journey_clicks.csv', 'mc_email_data', 'stg_eml_click', cfg)
            # execute separate load of exported Journey-based clicks information
            csv = CsvFile(**csv_args)
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

    def load_mc_journeys(self, **kwargs):
        token = self.__get_mc_auth(kwargs['data_source'])
        journeys = self.__get_mc_journeys(token)
        self.__load_mc_journeys_to_mongo(journeys, token)

    def __get_mc_auth(self, data_source):
        # TODO: resolve duplicated code in emails/services/classes/esp_push.py for images

        mc_data_config_args = self.get_mc_creds(data_source)

        # get auth token
        url = mc_data_config_args.get('auth_url')  # was 'https://auth.exacttargetapis.com/v1/requestToken'
        body = dict(clientId=mc_data_config_args.get('id'),  # was '3t1ch44ej7pb4p117oyr7m4g',
                    clientSecret=mc_data_config_args.get('secret'))  # was '2Cegvz6Oe9qTmc8HMUn2RWKh')
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

        # Build the service object
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

        # TODO: move this section to api_config
        filename = 'static/data/fips_codes_website.csv'
        if city_field is None:
            city_field = 'City'
        if state_field is None:
            state_field = 'Region'
        if dest_fips_code_field is None:
            fips_field = 'AreaCode'

        table_map = {'EmlOpen': EmlOpen,
                     'EmlClick': EmlClick}
        data_model = table_map.get(table, None)
        if table is None:
            return Exception('table not recognized or authorized to apply FIPS location code data to.')
        if self.db_session.query(data_model).count() == 0:
            print(f'No records in {table} Table. Append FIPS data terminated')
            return

        city = getattr(data_model, city_field)
        state = getattr(data_model, state_field)

        import csv
        with open(filename, 'r') as csvfile:
            csvfile_reader = csv.DictReader(csvfile, delimiter=',')
            already_processed = []

            # using city names without spaces
            for row in csvfile_reader:

                if (row['GU Name'], row['State Abbreviation']) in already_processed:
                    continue

                already_processed.append((row['GU Name'], row['State Abbreviation']))

                recs = self.db_session.query(data_model).filter(city == row['GU Name'].replace(' ', '').upper(),
                                          state == row['State Abbreviation']).all()
                # print('*', end='', flush=True)
                if len(recs) > 0:
                    print('found ' + str(len(recs)) + ' records with city ' + row['GU Name'].replace(' ', ''))
                    for rec in recs:
                        rec.__setattr__(fips_field, str(row['State FIPS Code'] + row['County FIPS Code']))
                        self.db_session.add(rec)
                    self.db_session.commit()

    def init_user_db(self, user_params, postgres_required=True):
        self.user_params = user_params
        print(user_params)

        postgres_uri = self.config.get(user_params.get('postgres_uri')) \
                       or user_params.get('postgres_uri')

        if postgres_required:
            if postgres_uri:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import scoped_session
                from sqlalchemy.orm import sessionmaker

                engine = create_engine(postgres_uri)
                self.db_session = scoped_session(sessionmaker(autoflush=False, bind=engine))
            else:
                raise Exception('Could not init user db')

        self.user_api_config = MongoUserApiConfigLoader(self.mongo.db, user_params).get_user_api_config()

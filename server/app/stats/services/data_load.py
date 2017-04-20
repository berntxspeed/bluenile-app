import requests
import traceback, sys
from pprint import pprint as pp 

from .classes.api_data import ApiData, ApiDataToSql, ApiDataToMongo
from .classes.ftp_file import ZipFile, CsvFile
from ...common.services import DbService
from ...common.models import EmlSend, EmlOpen, EmlClick, SendJob, Customer, Purchase, WebTrackingEvent, WebTrackingPageView, WebTrackingEcomm


class DataLoadService(DbService):

    def __init__(self, config, db, logger, mongo):
        super(DataLoadService, self).__init__(config, db, logger)
        self.mongo = mongo

    def exec_safe_session(self, load_func=None, *args):
        if load_func:
            try:
                load_func(*args)
            except:
                self.db.session.rollback()
            finally:
                self.db.session.remove()

    def load_customers(self):
        # load customer table here
        config = self.config
        customer_data_source = config.get('CUSTOMER_DATA_SOURCE')
        apicreds = config.get('EXT_DATA_CREDS')[customer_data_source]
        auth = (apicreds['id'], apicreds['secret'])
        endpoint = apicreds['endpoint']
        headers = {'Content-Type': 'application/json'}
        params = None #dict(ids='3211139395,3372597187')
        db_field_map = dict(customer_id='id',
                            email_address='email',
                            fname='first_name',
                            lname='last_name',
                            marketing_allowed='accepts_marketing',
                            created_at='created_at',
                            purchase_count='orders_count',
                            total_spent_so_far='total_spent')
        primary_keys = ['customer_id']
        json_data_keys = 'customers'

        ad1 = ApiDataToSql(endpoint=endpoint,
                      auth=auth,
                      headers=headers,
                      params=params,
                      db_session=self.db.session,
                      db_model=Customer,
                      primary_keys=primary_keys,
                      db_field_map=db_field_map,
                      json_data_keys=json_data_keys)

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
                      db_session=self.db.session,
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

    def load_purchases(self):
        config = self.config
        data_source = config.get('PURCHASE_DATA_SOURCE')
        apicreds = config.get('EXT_DATA_CREDS')[data_source]
        auth = (apicreds['id'], apicreds['secret'])
        endpoint = apicreds['endpoint']
        headers = {'Content-Type': 'application/json'}
        params = None  # dict(ids='3211139395,3372597187')
        db_field_map = dict(purchase_id='id',
                            customer_id='customer.id',
                            created_at='created_at',
                            price='total_price',
                            is_paid='financial_status',
                            referring_site='referring_site',
                            landing_site='landing_site',
                            browser_ip='browser_ip',
                            user_agent='client_details.user_agent')
        primary_keys = ['purchase_id']
        json_data_keys = 'orders'

        ad1 = ApiDataToSql(endpoint=endpoint,
                           auth=auth,
                           headers=headers,
                           params=params,
                           db_session=self.db.session(),
                           db_model=Purchase,
                           primary_keys=primary_keys,
                           db_field_map=db_field_map,
                           json_data_keys=json_data_keys)
        ad1.load_data()

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

        try:
            # load Sendjobs data to db
            zf.load_data(file='SendJobs.csv',
                         db_session=self.db.session,
                         db_model=SendJob,
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
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing SendJobs.csv'+traceback.print_tb(exc_traceback))
        try:
            zf.load_data(file='Sent.csv',
                         db_session=self.db.session,
                         db_model=EmlSend,
                         primary_keys=['SubscriberKey', 'EventDate'],
                         db_field_map={
                             'SendID': 'SendID',
                             'SubscriberKey': 'SubscriberKey',
                             'EmailAddress': 'EmailAddress',
                             'EventDate': 'EventDate'
                         },
                         chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Sent.csv'+traceback.print_tb(exc_traceback))
        try:
            # load Opens data to db
            zf.load_data(file='Opens.csv',
                         db_session=self.db.session,
                         db_model=EmlOpen,
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
                         },
                         chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Opens.csv'+traceback.print_tb(exc_traceback))
        try:
            # load Clicks data to db
            zf.load_data(file='Clicks.csv',
                         db_session=self.db.session,
                         db_model=EmlClick,
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
                         },
                         chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem importing Clicks.csv'+traceback.print_tb(exc_traceback))

        zf.clean_up() # delete downloaded files

        try:
            # execute separate load of exported Journey-based sends information
            filename = 'journey_sends.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db.session,
                          db_model=EmlSend,
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
            csv.load_data(chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_sends.csv'+traceback.print_tb(exc_traceback))
        try:
            # execute separate load of exported Journey-based opens information
            filename = 'journey_opens.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db.session,
                          db_model=EmlOpen,
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
            csv.load_data(chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_opens.csv'+traceback.print_tb(exc_traceback))
        try:
            # execute separate load of exported Journey-based clicks information
            filename = 'journey_clicks.csv'
            filepath = '/Export/'
            csv = CsvFile(file=filename,
                          db_session=self.db.session,
                          db_model=EmlClick,
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
            csv.load_data(chunk_size=10000)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('ALERT: problem loading journey_clicks.csv'+str(exc)+traceback.print_tb(exc_traceback))

        # TODO: append county FIPS codes to open and click data

        # append sent/open/click counts to SendJob rows
        sends = SendJob.query.all()
        for send in sends:
            send._get_stats()

    def load_mc_journeys(self):
        token = self.__get_mc_auth()
        journeys = self.__get_mc_journeys(token)
        self.__load_mc_journeys_to_db(journeys, token)

    def __get_mc_auth(self):
        #TODO: resolve duplicated code in emails/services/classes/esp_push.py for images
        config = self.config
        mc_data_creds = config.get('EXT_DATA_CREDS').get(config.get('EMAIL_DATA_DEST'))
        # get auth token
        url = mc_data_creds.get('auth_url') # was 'https://auth.exacttargetapis.com/v1/requestToken'
        body = dict(clientId=mc_data_creds.get('id'), # was '3t1ch44ej7pb4p117oyr7m4g',
                    clientSecret=mc_data_creds.get('secret')) # was '2Cegvz6Oe9qTmc8HMUn2RWKh')
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

    def __load_mc_journeys_to_db(self, journeys, token):

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
                print('problem with journey id ['+journey['id']+']')

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

            ad = ApiDataToSql(db_session=self.db.session,
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
                                   dims=('ga:pagePath', 'ga:deviceCategory', 'ga:mobileDeviceBranding', 'ga:mobileDeviceModel'),
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
        try:
            load_web_tracking_data(WebTrackingEvent,
                                   dims=('ga:eventAction', 'ga:deviceCategory', 'ga:mobileDeviceBranding', 'ga:mobileDeviceModel'),
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))
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
            print('failed one of the web tracking lookups: '+ str(exc))

    # this works with the fips_codes_website.csv file - which has the right FIPS values to match
    # - up with the ids of the us-10m.v1.json data from D3
    def add_fips_location_data(self, table, city_field=None, state_field=None, dest_fips_code_field=None):

        # how it works: it goes one by one through each FIPS code in the csv file
        # - and for each, searches the table for any records with that state/city
        # - and if it finds some, it throws the FIPS code on the field specified and saves back the records
        # - then moves on to the next


        filename = 'static/data/fips_codes_website.csv'
        db = self.db
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

                recs = model.query.filter(city == row['GU Name'].replace(' ', '').upper(),
                                          state == row['State Abbreviation']).all()
                # print('*', end='', flush=True)
                if len(recs) > 0:
                    print('found ' + str(len(recs)) + ' records with city ' + row['GU Name'].replace(' ', ''))
                    for rec in recs:
                        rec.__setattr__(fips_field, str(row['State FIPS Code'] + row['County FIPS Code']))
                        db.session.add(rec)
                    db.session.commit()

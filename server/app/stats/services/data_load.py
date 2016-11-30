import requests
from pprint import pprint as pp 

from .classes.api_data import ApiData, ApiDataToSql, ApiDataToMongo
from .classes.ftp_file import ZipFile
from ...common.services import DbService
from ...common.models import EmlSend, EmlOpen, EmlClick, SendJob, Artist, Customer, Purchase


class DataLoadService(DbService):

    def __init__(self, config, db, logger, mongo):
        super(DataLoadService, self).__init__(config, db, logger)
        self.mongo = mongo

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
                            total_spend_so_far='total_spent')
        primary_keys = ['customer_id']
        json_data_keys = ('customers',)

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
        json_data_keys = ('orders',)

        ad1 = ApiDataToSql(endpoint=endpoint,
                           auth=auth,
                           headers=headers,
                           params=params,
                           db_session=self.db.session,
                           db_model=Purchase,
                           primary_keys=primary_keys,
                           db_field_map=db_field_map,
                           json_data_keys=json_data_keys)
        ad1.load_data()

    def load_artists(self):
        artist_data_source = self.config.get('ARTIST_DATA_SOURCE')
        endpoint = self.config.get('EXT_DATA_CREDS')[artist_data_source]['endpoint']
        headers = {'Content-Type': 'application/json'}
        params = dict(q='year:2016', type='artist', market='us', limit=20)
        db_field_map = dict(name='name', popularity='popularity', uri='uri', href='href')
        primary_keys = ['name']
        json_data_keys = ('artists', 'items')

        ad = ApiDataToSql(endpoint=endpoint,
                          auth=None,
                          headers=headers,
                          params=params,
                          db_session=self.db.session,
                          db_model=Artist,
                          primary_keys=primary_keys,
                          db_field_map=db_field_map,
                          json_data_keys=json_data_keys)

        ad.load_data()
        pp(ad._get_data().keys())

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

        # load Sendjobs data to db
        zf.load_data(file='SendJobs.csv',
                     db_session=self.db.session,
                     db_model=SendJob,
                     primary_keys=['SendID'],
                     db_field_map={
                         'SendID': 'SendID',
                         'EmailName': 'EmailName',
                         'SchedTime': 'SchedTime',
                         'SentTime': 'SentTime',
                         'Subject': 'Subject',
                         'PreviewURL': 'PreviewURL'
                     })

        zf.load_data(file='Sent.csv',
                     db_session=self.db.session,
                     db_model=EmlSend,
                     primary_keys=['SubscriberKey', 'EventDate'],
                     db_field_map={
                         'SendID': 'SendID',
                         'SubscriberKey': 'SubscriberKey',
                         'EmailAddress': 'EmailAddress',
                         'EventDate': 'EventDate',
                         'TriggeredSendExternalKey': 'TriggeredSendExternalKey'
                     })

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
                         'TriggeredSendExternalKey': 'TriggeredSendExternalKey',
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
                         'TriggeredSendExternalKey': 'TriggeredSendExternalKey',
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
        zf.clean_up() # delete downloaded files

    def load_mc_journeys(self):
        token = self.__get_mc_auth()
        journeys = self.__get_mc_journeys(token)
        self.__load_mc_journeys_to_db(journeys, token)

    def __get_mc_auth(self):

        # get auth token
        url = 'https://auth.exacttargetapis.com/v1/requestToken'
        body = dict(clientId='pmbrqffimjnc2p9hfdnvg1sn',
                    clientSecret='R1HWMpHIpzqx0l2vp9glolND')
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
            adm = ApiDataToMongo(
                endpoint='https://www.exacttargetapis.com/interaction/v1/interactions/' + journey['id'],
                auth=None,
                headers={'Content-Type': 'application/json',
                         'Authorization': 'Bearer ' + token},
                params=None,
                collection=collection,
                primary_keys=['id'])
            adm.load_data()


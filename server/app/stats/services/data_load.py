from flask import url_for
from flask import flash
from flask import redirect
import requests
from pprint import pprint as pp 

from .classes.api_data import ApiData, ApiDataToSql, ApiDataToMongo
from .classes.ftp_file import ZipFile
from ...common.services import DbService
from ...common.models import User, EmlOpen, EmlClick, SendJob, Artist, Customer


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
        pp(ad1._get_data().keys())
        return redirect(url_for('stats.data_manager'))

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
        return redirect(url_for('stats.data_manager'))

    def load_mc_email_data(self):
        filename = 'upsell_campaign_tracking_extract.zip'
        cfg = {
            'host': 'ftp.s7.exacttarget.com',
            'username': '7228769',
            'password': 'Zx10@fxdl1997'
        }
        zf = ZipFile(file=filename,
                     ftp_path='/Export/',
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
        return redirect(url_for('stats.data_manager'))

    def load_mc_journeys(self):
        token = self.__get_mc_auth()
        journeys = self.__get_mc_journeys(token)
        self.__load_mc_journeys_to_db(journeys, token)
        return redirect(url_for('stats.data_manager'))

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


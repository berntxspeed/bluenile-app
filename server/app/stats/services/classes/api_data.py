import requests

from .db_data_loader import SqlDataLoader, MongoDataLoader


class ApiData(object):

    def __init__(self, endpoint, auth, headers, params):

        self._endpoint = endpoint
        self._auth = auth
        self._headers = headers
        self._params = params

    def get_data(self):
        # retrieves the data from the api endpoint
        response = requests.get(url=self._endpoint,
                                params=self._params,
                                headers=self._headers,
                                auth=self._auth)
        self._response = response
        if response.status_code != 200:
            raise ConnectionError('failed to retrieve data from api endpoint: ' + str(response.status_code))
        return response

class ApiDataToSql(ApiData, SqlDataLoader):
    """Retrieves data from a 'GET' api endpoint and loads to db table

    Params:
        endpoint: URI of api endpoint https://api.spotify.com/v1/search
        auth: authorization info for api
        params: options for api call, dict(option=value, option=value)
        db_model: object representing db table to load data to
        primary_keys: list of primary keys to respect on targeted table, ['pk1_field', 'pk2_field']
        db_field_map: dict mapping db_fields to fields in returned api data,
            ex. dict(dbfield1='apifield1', dbfield2='apifield2')
        json_data_keys: list of strings used to access the data in returned api call
            ex. data is { 'customers': [{cust1}, {cust2} ... ]}
                json_data_keys should be ['customers']

    Methods:
        load_data(): pulls data down from endpoint, and loads into db
    """

    def __init__(self, endpoint, auth, headers, params, db_session, db_model, primary_keys, db_field_map, json_data_keys=(None,)):

        SqlDataLoader.__init__(self,
                            db_session=db_session,
                            db_model=db_model,
                            primary_keys=primary_keys)

        ApiData.__init__(self, endpoint=endpoint,
                         auth=auth,
                         headers=headers,
                         params=params)

        self._json_data_keys = json_data_keys
        self._db_field_map = db_field_map

    def load_data(self):

        data = self._get_data()
        SqlDataLoader.load_to_db(self, data)

    def _get_data(self):

        response = ApiData.get_data(self)
        response = response.json()

        # access the desired data from the full response
        for jdk in self._json_data_keys:
            response = response[jdk]

        # create a dict of items for loading to db,
        # - key = composite(primarykeys)
        # - value = db_model instance
        data = {}
        for item in response:
            data_row = self._db_model()
            for db_field, api_field in self._db_field_map.items():
                data_row.__setattr__(db_field, item[api_field])
            comp_key = ''
            for pk in self._primary_keys:
                comp_key += str(getattr(data_row, pk))
            data[comp_key] = data_row

        return data


class ApiDataToMongo(ApiData, MongoDataLoader):

    def __init__(self, endpoint, auth, headers, params, collection, primary_keys, json_data_keys=None):

        ApiData.__init__(self, endpoint, auth, headers, params)
        MongoDataLoader.__init__(self, collection, primary_keys)

        self._json_data_keys = json_data_keys

    def load_data(self):

        data = self._get_data()
        MongoDataLoader.load_to_db(self, data)

    def _get_data(self):

        response = ApiData.get_data(self)
        response = response.json()

        # access the desired data from the full response
        if self._json_data_keys:
            for jdk in self._json_data_keys:
                response = response[jdk]

        return response

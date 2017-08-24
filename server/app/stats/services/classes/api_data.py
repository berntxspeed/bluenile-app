import requests

from .db_data_loader import SqlDataLoader, MongoDataLoader
from ....common.utils.db_datatype_handler import set_db_instance_attr


def json_select(json, selector):
    retval = None
    index = None

    field = selector.split('[')[0]
    if len(selector.split('[')) > 1:
        index = selector.split('[')[1][:-1]

    retval = json.get(field, None)

    if index is not None:
        if retval is None:
            raise ValueError('unable to access json at key: ' + str(field))
        retval = retval[int(index)]

    return retval


class ApiData(object):
    def __init__(self, endpoint, auth, headers, params, pagination=None, body_json=None):
        self._endpoint = endpoint
        self._auth = auth
        self._headers = headers
        self._params = params
        self._pagination = pagination
        self._body_json = body_json

    def get_data(self, http_method=None):

        if http_method is None:
            http_method = 'GET'

        if http_method is 'GET':
            if self._endpoint is not None:
                # retrieves the data from the api endpoint
                response = requests.get(url=self._endpoint,
                                        params=self._params,
                                        headers=self._headers,
                                        auth=self._auth)

            # only for Shopify
            elif self._pagination is not None:
                response = []

                last_timestamp = self._db_session.query(self._db_model).order_by((self._db_model.created_at.desc())).first()
                # no current records or not a Customer table
                if last_timestamp is None: #or self._db_model.__name__ != 'Customer':
                    print(f'No records in {self._db_model.__name__} Table... loading everything')
                    created_at_min = ''
                else:
                    max_timestamp = last_timestamp.created_at.isoformat()
                    created_at_min = f'created_at_min={max_timestamp}'
                    print(f'latest timestamp in {self._db_model.__name__} Table: {max_timestamp}')

                total_no_of_records_response = requests.get(url=f'{self._pagination["count_endpoint"]}',
                                                      params=self._params,
                                                      headers=self._headers,
                                                      auth=self._auth)

                no_of_records_response = requests.get(url=f'{self._pagination["count_endpoint"]}?{created_at_min}',
                                                      params=self._params,
                                                      headers=self._headers,
                                                      auth=self._auth)

                no_of_records = no_of_records_response.json().get(self._pagination['count_data_key'])
                total_no_of_records = total_no_of_records_response.json().get(self._pagination['count_data_key'])
                print(f'Getting {no_of_records} out of {total_no_of_records} records...')
                if no_of_records is None:
                    raise Exception('Failed to get records count: check credentials for your GET request')

                int_no_of_pages = int(no_of_records/self._pagination['records_limit'])
                if no_of_records/self._pagination['records_limit'] > int_no_of_pages:
                    number_of_pages = int_no_of_pages + 1
                else:
                    number_of_pages = int_no_of_pages
                for page_no in range(1, number_of_pages + 1):
                    page_url = f'{self._pagination["endpoint"]}{page_no}&{created_at_min}'
                    page_response = requests.get(url=page_url,
                                                 params=self._params,
                                                 headers=self._headers,
                                                 auth=self._auth)
                    response.append(page_response)

        elif http_method is 'POST':
            response = requests.post(url=self._endpoint,
                                     data=self._body_json,
                                     params=self._params,
                                     headers=self._headers,
                                     auth=self._auth)
        else:
            raise ValueError('illegal http_method: ' + http_method)

        self._response = response
        """if response.status_code != 200:
            raise ConnectionError(
                'Failed to retrieve data with {0} from api endpoint: {1}\n{2}'.format(str(response.status_code),
                                                                                      self._endpoint,
                                                                                      response.request.headers))"""
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

    def __init__(self, db_session, db_model, primary_keys, db_field_map,
                 endpoint=None, auth=None, headers=None, params=None,
                 json_data_keys=None, pagination=None, transform_response_data=None):

        SqlDataLoader.__init__(self,
                               db_session=db_session,
                               db_model=db_model,
                               primary_keys=primary_keys)

        if endpoint or pagination:
            ApiData.__init__(self, endpoint=endpoint,
                             auth=auth,
                             headers=headers,
                             params=params,
                             pagination=pagination)

        self._json_data_keys = json_data_keys
        self._db_field_map = db_field_map
        self._transform_response_data = transform_response_data

    def load_data(self, preload_data=None):

        SqlDataLoader.load_to_db(self, self._get_data, preload_data=preload_data)

    def _get_data(self, chunk_size=500, preload_data=None):
        num_recs = 0

        if preload_data is None:
            response = ApiData.get_data(self)
            if isinstance(response, list):
                response = [an_item.json() for an_item in response]
            else:
                response = response.json()
        else:
            response = preload_data

        # access the desired data from the full response
        if self._json_data_keys is not None:
            if isinstance(response, list):
                full_response = list()
                for response_page in response:
                    for jdk in self._json_data_keys.split('.'):
                        response_page = json_select(response_page, jdk)
                    full_response.append(response_page)

                response = [item for sublist in full_response for item in sublist]

            else:
                for jdk in self._json_data_keys.split('.'):
                    response = json_select(response, jdk)
                    # response = response[jdk]

        if self._transform_response_data:
            response = self._transpose_data(response)

        # create a dict of items for loading to db,
        # - key = composite(primarykeys)
        # - value = db_model instance
        data = {}
        if response is None:
            raise Exception('Empty response: no data to load. Check your data source config')

        for item in response:
            data_row = self._db_model()
            for db_field, api_field in self._db_field_map.items():
                data_row.__setattr__(db_field,
                                     set_db_instance_attr(data_row,
                                                          db_field,
                                                          str(self._get_json_field(item, api_field)))) #str(item[api_field]))
            comp_key = ''
            for pk in self._primary_keys:
                comp_key += str(getattr(data_row, pk))
            data[comp_key] = data_row

            num_recs += 1
            if num_recs >= chunk_size:
                num_recs = 0
                yield (False, data)
                data = {}

        yield (True, data)

    @staticmethod
    def _get_json_field(item, api_field):
        for field in api_field.split('.'):
            item = json_select(item, field)
            # item = item[field]
        return item

    @staticmethod
    def _transpose_data(data):
        """ Transforms a request into standard data format for SqlDataLoader
                -final format should be a list of dictionaries: records
                -temporary fix for zoho data load
        """
        record_data_key = 'FL'
        result = []
        for data_item in data:
            result_subitem = {}
            content_val_pairs = data_item[record_data_key]
            for a_content_val_pair in content_val_pairs:
                result_subitem[a_content_val_pair['val']] = a_content_val_pair['content']
            result.append(result_subitem)

        return result


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
            for jdk in self._json_data_keys.split('.'):
                response = json_select(response, jdk)

        return response

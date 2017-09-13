import base64
import json
import requests
import yaml

from FuelSDK import ET_Client, ET_Email
from server.app.common.models.user_models import Upload, Template
from server.app.stats.services.mongo_user_config_loader import MongoUserApiConfigLoader


class EmlPush(object):
    def __init__(self, config, mongo, db_session, key):

        self._config = config
        self._db_session = db_session
        self._mongo = mongo
        self._key = key
        self._id = None

        account_name = str(self._db_session.get_bind().url).split('/')[-1]
        self.user_api_config = MongoUserApiConfigLoader(self._mongo.db,
                                                        dict(account_name=account_name)).get_user_api_config()[-1]
        # The following  are credentials and api config params for MC
        self._api_config_file = self._config['API_CONFIG_FILE']
        self._data_load_config = self._load_config()
        self._et_client_params_map = {
                'clientid': 'id',
                'clientsecret': 'secret',
                'appsignature': 'signature',
                'defaultwsdl': 'default_wsdl',
                'authenticationurl': 'auth_url'
        }
        self._et_client_params = self._get_et_client_params(self.user_api_config, 'mc_journeys')

        # Marketing Cloud Specific
        debug = False
        self._stub_obj = ET_Client(False, debug, params=self._et_client_params)

    def _load_config(self):
        try:
            with open(self._api_config_file) as config_file:
                return yaml.load(config_file)
        except Exception:
            return {}

    def _get_et_client_params(self, user_config, data_source):
        et_client_params = {}
        user_api_config = None
        for vendor_user_config in user_config:
            if vendor_user_config.get('data_source') == data_source:
                user_api_config = vendor_user_config
                break

        if not user_api_config:
            raise Exception('Lacking MC credentials: data push is not supported')

        user_api_config.update(self._data_load_config['mc_journeys']['fuelsdk_config'])
        for k, v in self._et_client_params_map.items():
            et_client_params[k] = user_api_config[v]

        return et_client_params

    def sync_to_ems(self):

        # grab email from db
        template = self._db_session.query(Template).filter_by(key=self._key).first()
        if template is None:
            raise ValueError('no template at specified key exists: ' + self._key)

        # email creation
        if not self._check_email_exists():
            resp = self._push_email('create', template)
        else:
            resp = self._push_email('update', template)

        if resp.code is not None and resp.code != 200:
            return resp

        return resp

    def _check_email_exists(self):

        eml = ET_Email()
        eml.auth_stub = self._stub_obj
        eml.props = ['ID', 'Name', 'CustomerKey']
        eml.search_filter = {'Property': 'CustomerKey', 'SimpleOperator': 'equals', 'Value': self._key}

        resp = eml.get()

        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when accessing email object')
        if len(resp.results) > 1:
            raise ValueError('there should only be one email object with that particular customer key value: ' + self._name)
        if len(resp.results) == 0:
            return False # to indicate that 'no' the email does not exist in Marketing Cloud at the moment
        if resp.results[0].CustomerKey == self._key:
            self._id = resp.results[0].ID
            return True # to indicate that 'yes' the email does exist in Marketing Cloud at the moment
        # if no return conditions were meant something went off the rails,
        # - so raise an exception
        raise ValueError('none of the conditions were met in attempting to determine if email exists in marketing cloud')

    def _push_email(self, action, template):

        allowed_actions = ['create', 'update']
        if action not in allowed_actions:
            raise ValueError('Illegal action used for _push_email() call')

        props = {
            'CustomerKey': self._key,
            'Name': template.name,
            'Subject': '***update me***',
            'HTMLBody': template.html,
            'EmailType': 'HTML',
            'IsHTMLPaste': 'true'
        }
        if self._id is not None:
            # in case of email update, must pass ID along too
            props['ID'] = self._id

        eml = ET_Email()
        eml.auth_stub = self._stub_obj
        eml.props = props

        if action == 'create':
            resp = eml.post()
        elif action == 'update':
            resp = eml.patch()
        else:
            raise ValueError('Illegal action used for _push_email() call')

        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when attempting to push email' + str(resp.results))
        if resp.message != 'OK':
            raise ValueError('error occurred while pushing email' + resp.message + resp.status + resp.code)
        return resp


class ImgPush(object):

    def __init__(self, db_session, file, filename):
        self._db_session = db_session
        self._file = file
        self._filename = filename
        self._esp_hosted_url = None
        self._esp_hosted_key = None
        self._esp_hosted_id = None
        self._esp_hosted_category_id = None
        self._image_size_width = None
        self._image_size_height = None

    def save(self):
        resp = None
        http_status_code = None

        try:
            if self._is_already_uploaded_to_esp():
                self._push_to_esp('update')
            else:
                self._push_to_esp('insert')
            if self._esp_hosted_url is None:
                raise ValueError('self._esp_hosted_url cannot be empty')
            self._save_to_db()
            resp = {
                'deleteType': 'DELETE',
                'deleteUrl': self._esp_hosted_url,
                'name': self._filename,
                'originalName': self._filename,
                'size': (self._image_size_width, self._image_size_height),
                'thumbnailUrl': self._esp_hosted_url,
                'type': None,
                'url': self._esp_hosted_url
            }
            http_status_code = 201
        except ValueError as exc:
            resp = dict(error=str(exc))
            http_status_code = 500

        return resp, http_status_code

    def _is_already_uploaded_to_esp(self):
        upload = self._db_session.query(Upload).filter_by(name=self._filename).first()
        if upload is not None:
            if upload.esp_hosted_key is not None:
                self._esp_hosted_key = upload.esp_hosted_key
                self._esp_hosted_id = upload.esp_hosted_id
                self._esp_hosted_category_id = upload.esp_hosted_category_id
                self._image_size_width = upload.image_size_width
                self._image_size_height = upload.image_size_height
                return True
        return False

    def _save_to_db(self):
        # insert or update
        upload = self._db_session.query(Upload).filter_by(name=self._filename).first()
        if upload is not None:
            self._file.seek(0)
            upload.image = self._file.read()
            upload.esp_hosted_url = self._esp_hosted_url
            upload.esp_hosted_key = self._esp_hosted_key
            upload.esp_hosted_id = self._esp_hosted_id
            upload.esp_hosted_category_id = self._esp_hosted_category_id
            upload.image_size_height = self._image_size_height
            upload.image_size_width = self._image_size_width
        else:
            self._file.seek(0)
            upload = Upload(name = self._filename,
                            image = self._file.read(),
                            esp_hosted_url = self._esp_hosted_url,
                            esp_hosted_key = self._esp_hosted_key,
                            esp_hosted_id = self._esp_hosted_id,
                            esp_hosted_category_id = self._esp_hosted_category_id,
                            image_size_width = self._image_size_width,
                            image_size_height = self._image_size_height)
        self._db_session.add(upload)
        self._db_session.commit()

    def _push_to_esp(self, action):
        if action in ['insert', 'update']:
            token = self.__get_auth_from_esp()
            if action is 'insert':
                upload = self.__push_file_to_esp(token, method='POST')
            elif action is 'update':
                upload = self.__push_file_to_esp(token, method='PUT')
            self._esp_hosted_key = upload.get('customerKey', None)
            self._esp_hosted_id = upload.get('id', None)
            category = upload.get('category', None)
            if category is not None:
                self._esp_hosted_category_id = category.get('id')
            fileProperties = upload.get('fileProperties')
            if fileProperties is not None:
                self._esp_hosted_url = fileProperties.get('publishedURL')
                self._image_size_width = fileProperties.get('width')
                self._image_size_height = fileProperties.get('height')
            print(upload)
        else:
            raise ValueError('illegal action selected for _push_to_esp() call')

    def _img_to_b64(self):
        self._file.seek(0)
        return base64.b64encode(self._file.read())

    def _get_asset_type_details(self):
        IDS = {'gif': 20, 'jpeg': 22, 'jpg': 23, 'bmp': 32, 'svg': 39, 'png': 28}
        file_ext = self._filename.split('.')[-1]
        asset_type_id = IDS.get(file_ext, None)
        if asset_type_id is None:
            raise ValueError('invalid file type, not in list of accepted filetypes')
        return file_ext, asset_type_id

    def __get_auth_from_esp(self):
        # TODO: resolve duplicated code in emails/services/classes/esp_push.py for images
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

    def __push_file_to_esp(self, token, method='POST'):
        file_ext, asset_type_id = self._get_asset_type_details()
        request_body = dict(name=''.join(self._filename.split('.')[:-1]),
                    assetType=dict(name=file_ext,
                                   id=asset_type_id),
                    file=self._img_to_b64().decode())
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }

        if method in ['POST', 'PUT']:
            if method is 'POST':
                url = 'https://www.exacttargetapis.com/asset/v1/content/assets'
                r = requests.post(url, data=json.dumps(request_body), headers=headers)
            elif method is 'PUT':
                url = 'https://www.exacttargetapis.com/asset/v1/content/assets/' + str(self._esp_hosted_id)
                request_body['customerKey'] = self._esp_hosted_key
                request_body['id'] = self._esp_hosted_id
                request_body['category'] = dict(id=self._esp_hosted_category_id, parentId=0, name='Content Builder')
                r = requests.patch(url, data=json.dumps(request_body), headers=headers)
            if r.status_code < 200 or r.status_code > 250:
                raise ConnectionError('error, failed to push file to esp: ' + str(r.content))
            return r.json()
        else:
            raise ValueError('illegal method passed for __push_file_to_esp call')


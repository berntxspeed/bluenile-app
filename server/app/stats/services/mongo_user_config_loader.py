import datetime
import os
import sys

from cryptography.fernet import Fernet
from ...stats.services.classes.db_data_loader import MongoDataLoader

DEFAULT_ENCODING = sys.getdefaultencoding()

# KEY = bytes(os.getenv('VENDOR_APIS_CIPHER_KEY'), DEFAULT_ENCODING)
CIPHER_KEY = bytes('superrandombluenilecipherkeysforvendorsapis=', DEFAULT_ENCODING)

SYNC_MAP = {
    "0": "Never",
    "1": "Every X Hour(s)",
    "2": "Daily",
    "3": "Every Weekday",
    "4": "Every M, W, Fri",
    "5": "Every Tue, Thu",
    "6": "Weekly",
    "7": "Monthly",
    "8": "Annually"
}

VENDOR_API_TO_TABLES_MAP = {
    'shopify': ['customer', 'purchase'],
    'magento': ['customer', 'purchase'],
    'bigcommerce': ['customer', 'purchase'],
    'stripe': ['customer'],
    'x2crm': ['customer'],
    'mc_email_data': ['mc_email_data'],
    'zoho': ['customer']
}


class MongoDataJobConfigLoader(object):
    def __init__(self, client_instance, user_config=None):
        self._db = client_instance
        self._collection_name = 'data_load_jobs'
        self._primary_key = 'job_type'
        self._user_config = user_config

        user_account = self._user_config and self._user_config.get('account_name')
        if user_account:
            self._collection_name = self._collection_name + '_' + user_account
        self._collection = self._db[self._collection_name]

    def get_data_load_jobs(self):
        all_data_load_jobs = []
        try:
            for a_config in self._collection.find({}, {'_id': 0}):
                all_data_load_jobs.append(a_config)

            self.convert_fields(all_data_load_jobs)
            return True, all_data_load_jobs
        except Exception as e:
            return False, 'Getting Data Load Job Config Failed: {0}'.format(str(e))

    @staticmethod
    def convert_fields(dl_jobs):
        for a_dl_job in dl_jobs:
            if a_dl_job.get('job_type'):
                a_dl_job['job_type_full'] = a_dl_job['job_type'].replace('_', ' ').title()
            if a_dl_job.get('periodic_sync'):
                if a_dl_job['periodic_sync'] == '1':
                    a_dl_job['frequency'] = str(SYNC_MAP[a_dl_job['periodic_sync']]
                                               .replace('X', a_dl_job.get('hourly_frequency', 'X')))
                else:
                    a_dl_job['frequency'] = str(SYNC_MAP[a_dl_job['periodic_sync']])

    def save_data_load_config(self, dl_job_config, update=False):
        """Use this method to setup data load job config """
        if not update:
            dl_job_config['timestamp'] = str(datetime.datetime.now())

        item_loader = MongoDataLoader(self._collection, [self._primary_key])
        try:
            item_loader.load_to_db(dl_job_config)
            return True, True
        except Exception as e:
            return False, 'Saving Data Load Job Config Failed: {0}'.format(str(e))

    def remove_data_load_config_by_data_source(self, data_source):
        try:
            self._collection.remove({'data_source': data_source})
            return True, True
        except Exception as e:
            return False, 'Removing Data Load Config Failed: {0}'.format(str(e))

    def get_data_load_config_by_type(self, job_type):
        try:
            data_load_config = self._collection.find( { self._primary_key: job_type } , { '_id': 0 } )[0]
            return True, data_load_config
        except Exception as e:
            return False, 'Getting Data Load Config Failed: {0}'.format(str(e))

    def update_last_load_info(self, job_type):
        import datetime
        status, load_job_config = self.get_data_load_config_by_type(job_type.replace('load_', ''))
        if status is False:
            return status, load_job_config
        last_load = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        load_job_config['last_run'] = last_load
        return self.save_data_load_config(load_job_config, update=True)

    def create_default_config(self, data_source):
        for a_data_type in VENDOR_API_TO_TABLES_MAP.get(data_source, []):
            default_config = dict(data_source=data_source)
            default_config['data_type'] = a_data_type
            default_config['job_type'] = '{0}_{1}s'.format(data_source, a_data_type)
            self.save_data_load_config(default_config)


class MongoUserApiConfigLoader(object):
    def __init__(self, client_instance, user_config=None):
        self._db = client_instance
        self._collection_name = 'user_api_config'
        self._primary_key = 'data_source'
        self._user_config = user_config

        user_account = self._user_config and self._user_config.get('account_name')
        if user_account:
            self._collection_name = self._collection_name + '_' + user_account
        self._collection = self._db[self._collection_name]

    @staticmethod
    def encrypt(str_to_encode):
        """Encrypt the string and return the ciphertext"""
        cipher_suite = Fernet(CIPHER_KEY)
        b_format = bytes(str_to_encode, DEFAULT_ENCODING)
        result = cipher_suite.encrypt(b_format).decode(DEFAULT_ENCODING)
        return result

    @staticmethod
    def decrypt(ciphertext):
        """Decrypt the string and return the secret"""
        cipher_suite = Fernet(CIPHER_KEY)
        b_format = bytes(ciphertext, DEFAULT_ENCODING)
        result = cipher_suite.decrypt(b_format).decode(DEFAULT_ENCODING)
        return result

    def get_user_api_config(self):
        all_vendors = []
        try:
            for vendor_config in self._collection.find({}, {'_id': 0}).sort('timestamp', -1):
                for k, v in vendor_config.items():
                    if k in ['domain', 'token', 'secret', 'id']:
                        vendor_config[k] = MongoUserApiConfigLoader.decrypt(v)
                all_vendors.append(vendor_config)

            return True, all_vendors
        except Exception as e:
            return False, 'Getting User API Config Failed: {0}'.format(str(e))

    def save_api_config(self, vendor_config, update=False):
        """Use this method to setup user api config """
        if not vendor_config:
            return False, 'Cannot Save Empty Api Config'
        if not update:
            for k, v in vendor_config.items():
                if k in ['domain', 'token', 'secret', 'id']:
                    vendor_config[k] = MongoUserApiConfigLoader.encrypt(v)

            vendor_config['timestamp'] = str(datetime.datetime.now())
            MongoDataJobConfigLoader(self._db, self._user_config).create_default_config(vendor_config['data_source'])

        item_loader = MongoDataLoader(self._collection, [self._primary_key])
        try:
            item_loader.load_to_db(vendor_config)
            return True, True
        except Exception as e:
            return False, 'Saving Vendor Config Failed: {0}'.format(str(e))

    def get_data_config_by_source(self, data_source):
        try:
            data_config = self._collection.find( { self._primary_key: data_source } , { '_id': 0 } )[0]
            return True, data_config
        except Exception as e:
            return False, 'Getting Data Config Failed: {0}'.format(str(e))

    def remove_api_config_by_source(self, data_source):
        try:
            self._collection.remove({self._primary_key: data_source})
            return MongoDataJobConfigLoader(self._db, self._user_config).remove_data_load_config_by_data_source(data_source)
        except Exception as e:
            return False, 'Removing Data Load Config Failed: {0}'.format(str(e))

    def update_last_run_info(self, data_source):
        import datetime
        status, data_config = self.get_data_config_by_source(data_source)
        last_load = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        data_config['last_run'] = last_load
        return self.save_api_config(data_config, update=True)

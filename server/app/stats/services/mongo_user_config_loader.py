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


class MongoDataJobConfigLoader(object):
    def __init__(self, client_instance):
        self._db = client_instance
        self._collection_name = 'data_load_jobs'
        self._collection = self._db[self._collection_name]
        self._primary_key = 'job_type'

    def get_data_load_jobs(self):
        all_data_load_jobs = []
        try:
            for a_config in self._collection.find({}, {'_id': 0}):
                all_data_load_jobs.append(a_config)

            self.convert_frequency(all_data_load_jobs)
            return True, all_data_load_jobs
        except Exception as e:
            return False, 'Getting Data Load Job Config Failed: {0}'.format(str(e))

    @staticmethod
    def convert_frequency(dl_jobs):
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

    def get_data_load_config_by_type(self, job_type):
        try:
            data_load_config = self._collection.find( { self._primary_key: job_type } , { '_id': 0 } )[0]
            return True, data_load_config
        except Exception as e:
            return False, 'Getting Data Load Config Failed: {0}'.format(str(e))

    def update_last_load_info(self, job_type):
        import datetime
        status, load_job_config = self.get_data_load_config_by_type(job_type.replace('load_', ''))
        last_load = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        load_job_config['last_run'] = last_load
        return self.save_data_load_config(load_job_config, update=True)


class MongoUserApiConfigLoader(object):
    def __init__(self, client_instance):
        self._db = client_instance
        self._collection_name = 'user_api_config'
        self._collection = self._db[self._collection_name]
        self._primary_key = 'data_source'

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
        if not update:
            for k, v in vendor_config.items():
                if k not in ['data_source']:
                    vendor_config[k] = MongoUserApiConfigLoader.encrypt(v)

            vendor_config['timestamp'] = str(datetime.datetime.now())
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

    def update_last_run_info(self, data_source):
        import datetime
        status, data_config = self.get_data_config_by_source(data_source)
        last_load = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        data_config['last_run'] = last_load
        return self.save_api_config(data_config, update=True)

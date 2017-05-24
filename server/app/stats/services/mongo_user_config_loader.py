import datetime
import os
import sys

from cryptography.fernet import Fernet
from ...stats.services.classes.db_data_loader import MongoDataLoader

DEFAULT_ENCODING = sys.getdefaultencoding()

# KEY = bytes(os.getenv('VENDOR_APIS_CIPHER_KEY'), DEFAULT_ENCODING)
CIPHER_KEY = bytes('superrandombluenilecipherkeysforvendorsapis=', DEFAULT_ENCODING)


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
                    if k not in ['data_source', 'timestamp']:
                        vendor_config[k] = MongoUserApiConfigLoader.decrypt(v)
                all_vendors.append(vendor_config)

            return True, all_vendors
        except Exception as e:
            return False, 'Getting User API Config Failed: {0}'.format(str(e))

    def save_api_config(self, vendor_config):
        """Use this method to setup user api config"""
        item_loader = MongoDataLoader(self._collection, [self._primary_key])
        for k, v in vendor_config.items():
            if k not in ['data_source']:
                vendor_config[k] = MongoUserApiConfigLoader.encrypt(v)

        vendor_config['timestamp'] = str(datetime.datetime.now())
        try:
            item_loader.load_to_db(vendor_config)
            return True, True
        except Exception as e:
            return False, 'Saving Vendor Config Failed: {0}'.format(str(e))

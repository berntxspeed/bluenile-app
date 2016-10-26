from FuelSDK import ET_Client, ET_DataExtension
from sqlalchemy import inspect



class DataPusher(object):

    def __init__(self, db, model):
        self._db = db
        self._model = model
        self._tablename = model.__tablename__

        # Marketing Cloud Specific
        debug = False
        self._stubObj = ET_Client(False, debug)

    def sync_table(self):
        if not self._check_table_exists():
            resp = self._create_table()

    def _check_table_exists(self):
        de = ET_DataExtension()
        de.props = ['CustomerKey', 'Name']
        de.auth_stub = self._stubObj
        de.search_filter = {'Property': 'CustomerKey', 'SimpleOperator': 'equals', 'Value': self._tablename}
        resp = de.get()
        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when accessing data extensions')
        if len(resp.results) > 1:
            raise ValueError('there should only be one data extension with that particular customer key value: ' + self._tablename)
        if len(resp.results) == 0:
            return False # to indicate that 'no' the table does not exist in Marketing Cloud at the moment
        if resp.results[0].CustomerKey == self._tablename:
            return True # to indicate that 'yes' the table does exist in Marketing Cloud at the moment
        # if no return conditions were meant something went off the rails,
        # - so raise an exception
        raise ValueError('none of the conditions were met in attempting to determine if table exists in marketing cloud')

    def _create_table(self):
        de = ET_DataExtension()
        de.auth_stub = self._stubObj
        de.props = {'Name': self._tablename, 'CustomerKey': self._tablename}
        de.columns = []
        for column, value in self._model.__dict__.items():

            if column[0] != '_':

                new_column = {
                    'Name': column
                }

                if self.__check_primary_key(column):
                    new_column['IsPrimaryKey'] = 'true'
                    new_column['IsRequired'] = 'false'
                else:
                    new_column['IsPrimaryKey'] = 'false'
                    new_column['IsRequired'] = 'false'

                if self.__check_date_type(column):
                    new_column['FieldType'] = 'date'
                else:
                    new_column['FieldType'] = 'time'
                    new_column['MaxLength'] = '255'

                de.columns.append(new_column)

        resp = de.post()

        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when attempting to create data extension' + str(resp))
        if resp.message != 'OK':
            raise ValueError('error occured while created data extension' + resp.message + resp.status + resp.code)
        return resp

    def __check_primary_key(self, column):
        ins = inspect(self._model)
        for pk_column in ins.primary_key:
            if pk_column.key == column:
                return True
        return False

    def __check_date_type(self, column):
        ins = inspect(self._model)
        for ins_column in ins.columns:
            if ins_column == column:
                if str(ins_column.type) == 'TIMESTAMP WITHOUT TIME ZONE':
                    return True
        return False




import logging
from FuelSDK import ET_Client, ET_DataExtension, ET_DataExtension_Row
from sqlalchemy import inspect
import time
import datetime


class DataPusher(object):

    def __init__(self, db, model):
        self._db = db
        self._model = model
        self._tablename = model.__tablename__

        # Marketing Cloud Specific
        debug = False
        self._stub_obj = ET_Client(False, debug)

    def sync_table(self):
        resp = 'no operation performed'

        # table creation
        if not self._check_table_exists():
            resp = self._create_table()
            if resp.code is not None and resp.code != 200:
                return resp

        # table inserts
        recs = self._find_recs_for_insert()
        if len(recs) > 0:
            resp = self._push_de_recs(recs, 'insert')
            if resp.code and resp.code != 200:
                return resp
            msg = 'inserted ' + str(len(recs)) + ' records'
            logging.info(msg)

        # table updates
        recs = self._find_recs_for_update()
        if len(recs) > 0:
            resp = self._push_de_recs(recs, 'update')
            if resp.code and resp.code != 200:
                return resp
            msg = 'updated ' + str(len(recs)) + ' records'
            logging.info(msg)

        return resp

    def sync_query(self, name, query):
        # ***check that query returned model = self._model

        # table creation
        if not self._check_table_exists(name):
            resp = self._create_table(name)
            if resp.code is not None and resp.code != 200:
                return resp

        # table inserts
        recs = query.all()
        if len(recs) > 0:
            resp = self._push_de_recs(recs,
                                      name,
                                      update_or_insert='insert',
                                      options=['no_timestamp'])
            if resp.code is not None and resp.code != 200:
                return resp
            msg = 'inserted ' + str(len(recs)) + ' records'
            logging.info(msg)

        return resp

    def _check_table_exists(self, name=None):
        # checks if the table exists in Marketing Cloud
        # returns: False if no table, True if table exists

        name = name or self._tablename

        de = ET_DataExtension()
        de.props = ['CustomerKey', 'Name']
        de.auth_stub = self._stub_obj
        de.search_filter = {'Property': 'CustomerKey', 'SimpleOperator': 'equals', 'Value': name}
        resp = de.get()
        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when accessing data extensions')
        if len(resp.results) > 1:
            raise ValueError('there should only be one data extension with that particular customer key value: ' + self._tablename)
        if len(resp.results) == 0:
            return False # to indicate that 'no' the table does not exist in Marketing Cloud at the moment
        if resp.results[0].CustomerKey == name:
            return True # to indicate that 'yes' the table does exist in Marketing Cloud at the moment
        # if no return conditions were meant something went off the rails,
        # - so raise an exception
        raise ValueError('none of the conditions were met in attempting to determine if table exists in marketing cloud')

    def _create_table(self, name=None):

        if name is None:
            name = self._tablename

        de = ET_DataExtension()
        de.auth_stub = self._stub_obj
        de.props = {'Name': name, 'CustomerKey': name}
        columns = []
        for column, value in self._model.__dict__.items():

            if column[0] != '_':

                new_column = {
                    'Name': column
                }

                if self.__check_primary_key(column):
                    new_column['IsPrimaryKey'] = 'true'
                    new_column['IsRequired'] = 'true'
                else:
                    new_column['IsPrimaryKey'] = 'false'
                    new_column['IsRequired'] = 'false'

                if self.__check_date_type(column):
                    new_column['FieldType'] = 'Date'
                else:
                    new_column['FieldType'] = 'Text'
                    new_column['MaxLength'] = '255'

                columns.append(new_column)

        de.columns = columns
        resp = de.post()

        if resp.code != 200:
            raise ConnectionError('failed to receive response from Marketing Cloud when attempting to create data extension' + str(resp.results))
        if resp.message != 'OK':
            raise ValueError('error occurred while created data extension' + resp.message + resp.status + resp.code)
        return resp

    def _find_recs_for_insert(self):
        Model = self._model
        recs = Model.query.filter(Model._last_ext_sync == None)
        return recs

    def _find_recs_for_update(self):
        Model = self._model
        recs = Model.query.filter(Model._last_ext_sync != None,
                                  Model._last_ext_sync + datetime.timedelta(minutes=1)
                                  < Model._last_updated)
        return recs

    def _push_de_recs(self, recs, name, update_or_insert, options=None):

        name = name or self._tablename

        ALLOWABLE_OPERATIONS = ['update', 'insert']
        ALLOWABLE_OPTIONS = ['no_timestamp']

        if update_or_insert not in ALLOWABLE_OPERATIONS:
            raise ValueError('invalid operation selected: ' + str(update_or_insert))
        if options is not None and isinstance(options, list):
            for option in options:
                if option not in ALLOWABLE_OPTIONS:
                    raise ValueError('invalid option selected: ' + str(option))

        resp = None

        de = ET_DataExtension_Row()
        de.auth_stub = self._stub_obj
        de.CustomerKey = name
        de.Name = name

        for rec in recs:

            de.props = {}
            for column, value in self._model.__dict__.items():
                if column[0] != '_':
                    de.props[column] = getattr(rec, column)

            if update_or_insert == 'insert':
                resp = de.post()

            if update_or_insert == 'update':
                resp = de.patch()

            # Early return in case of an errored api call
            if resp.code != 200:
                print('error making api call for record: ' + str(rec))
                break

            if 'no_timestamp' not in options:
                rec._update_last_ext_sync()
                self._db.session.add(rec)

        self._db.session.commit()
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
            if str(ins_column.name) == str(column):
                if str(ins_column.type) == 'TIMESTAMP WITHOUT TIME ZONE':
                    return True
        return False

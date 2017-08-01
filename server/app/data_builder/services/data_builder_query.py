from ...stats.services.classes.db_data_loader import MongoDataLoader

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


class DataBuilderQuery(object):
    def __init__(self, client_instance, user_config=None):
        self._db = client_instance
        self._primary_key = 'name'
        self._collection_name = 'data_builder_qs'

        user_account = user_config and user_config.get('account_name')
        if user_account:
            self._collection_name = self._collection_name + '_' + user_account

        self._collection = self._db[self._collection_name]

    @staticmethod
    def convert_date_and_frequency_to_human_readable(all_queries):
        for a_query in all_queries:
            #iso_to_date
            if a_query.get('created'):
                a_query['created'] = str(a_query['created']).replace('T', ' at ')[:-5]
            if a_query.get('periodic_sync'):
                if a_query['periodic_sync'] == '1':
                    a_query['frequency'] = str(SYNC_MAP[a_query['periodic_sync']]
                                               .replace('X', a_query.get('hourly_frequency', 'X')))
                else:
                    a_query['frequency'] = str(SYNC_MAP[a_query['periodic_sync']])

    @staticmethod
    def date_to_iso(current_date):
        iso_date = current_date.replace(' at ', 'T') + '0'*5
        return iso_date

    def get_all_queries(self, type=None):
        all_queries = []
        if type == 'default':
            filter_func = lambda q: 'preset' in q
        elif type == 'all':
            filter_func = None
        elif type == 'auto_sync':
            filter_func = lambda q: q.get('auto_sync') is True
        else:
            filter_func = lambda q: 'preset' not in q

        try:
            for a_query in filter(filter_func, self._collection.find({}, {'_id': 0}).sort('created', -1)):
                all_queries.append(a_query)

            self.convert_date_and_frequency_to_human_readable(all_queries)
            return True, all_queries
        except Exception as e:
            return False, 'Get All Queries Failed: {0}'.format(str(e))

    def save_query(self, query_name, search_query):
        if 'at' in search_query.get('created'):
            search_query['created'] = self.date_to_iso(search_query['created'])
        search_query[self._primary_key] = query_name
        item_loader = MongoDataLoader(self._collection, [self._primary_key])
        try:
            item_loader.load_to_db(search_query)
            return True, True
        except Exception as e:
            return False, 'Saving Query Failed: {0}'.format(str(e))

    def get_query_by_name(self, query_name):
        try:
            query = self._collection.find( { self._primary_key: query_name } , { '_id': 0 } )[0]
            return True, query
        except Exception as e:
            return False, 'Getting Query Failed: {0}'.format(str(e))

    def remove_query(self, query_name):
        try:
            self._collection.remove({self._primary_key: query_name})
            return True, True
        except Exception as e:
            return False, 'Removing Query Failed: {0}'.format(str(e))

    def update_last_run_info(self, query_name):
        import datetime
        status, query = self.get_query_by_name(query_name)
        last_sync = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        query['last_run'] = last_sync
        return self.save_query(query_name, query)
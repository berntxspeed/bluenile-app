from ...stats.services.classes.db_data_loader import MongoDataLoader


class DataBuilderQuery(object):
    def __init__(self, client_instance):
        self._primary_key = 'name'
        self._collection_name = 'data_builder_qs'

        self._db = client_instance
        self._collection = self._db[self._collection_name]

    @staticmethod
    def iso_to_date(all_queries):
        for a_query in all_queries:
            if a_query.get('created'):
                a_query['created'] = str(a_query['created']).replace('T', ' at ')[:-5]

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
        else:
            filter_func = lambda q: 'preset' not in q

        try:
            for a_query in filter(filter_func, self._collection.find({}, {'_id': 0}).sort('created', -1)):
                all_queries.append(a_query)

            self.iso_to_date(all_queries)
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
        query['last_sync'] = last_sync
        return self.save_query(query_name, query)

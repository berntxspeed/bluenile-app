from server.app.stats.services.classes.db_data_loader import MongoDataLoader


class DataBuilderQuery(object):
    def __init__(self, client_instance):
        self._primary_key = 'name'
        self._collection_name = 'data_builder_qs'

        self._db = client_instance
        self._collection = self._db[self._collection_name]

    @staticmethod
    def convert_timedate(all_queries):
        for a_query in all_queries:
            if a_query.get('created'):
                a_query['created'] = str(a_query['created']).replace('T', ' at ')[:-5]

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

            self.convert_timedate(all_queries)
            return True, all_queries
        except Exception as e:
            return False, 'Get All Queries Failed: {0}'.format(str(e))

    def save_query(self, query_name, search_query):
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
# from server.app.stats.services.classes.db_data_loader import MongoDataLoader
from server.app.stats.services.classes.db_data_loader import MongoDataLoader


class DataBuilderQuery(object):
    def __init__(self, client_instance):
        self._primary_key = 'name'
        self._db_name = 'simple_di_flask_dev'
        self._collection_name = 'data_builder_qs'

        self._db = client_instance[self._db_name]
        self._collection = self._db[self._collection_name]

    def get_all_queries(self):
        all_queries = []
        try:
            for a_query in self._collection.find():
                # remove the _id to prevent information leak to UI
                del a_query['_id']
                all_queries.append(a_query)

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
            query = self._collection.find( { self._primary_key: query_name } )[0]
            del query['_id']
            return True, query
        except Exception as e:
            return False, 'Getting Query Failed: {0}'.format(str(e))

    def remove_query(self, query_name):
        try:
            self._collection.remove({self._primary_key: query_name})
            return True, True
        except Exception as e:
            return False, 'Removing Query Failed: {0}'.format(str(e))

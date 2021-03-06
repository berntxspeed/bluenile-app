from flask import logging

logger = logging.getLogger(__name__)


class SqlDataLoader(object):
    def __init__(self, db_session, db_model, primary_keys, db_processing_chunk_size=500):

        self._db_session = db_session
        self._db_model = db_model
        self._primary_keys = primary_keys
        self._db_processing_chunk_size = db_processing_chunk_size

    def db_model(self, **kwargs):

        return self._db_model(**kwargs)

    def load_to_db(self, items):

        """
            primary_keys should be a list of strings of primary key field name to search for
            items should be a dict where key=str(primary key) value and value is the model instance
        """

        update_cnt = 0  # keep track of updated records

        # build sqlalchemy composite key expression for use in finding pre-existing records
        model_composite_key = getattr(self._db_model, self._primary_keys[0])
        for pk in self._primary_keys[1:]:
            model_composite_key = model_composite_key.concat(getattr(self._db_model, pk))

        composite_key_list = list(items.keys())
        chunk_size = self._db_processing_chunk_size
        for chunk in range(1, int(len(composite_key_list) / chunk_size) + 2):

            start_index = int((chunk - 1) * chunk_size)
            end_index = int((chunk * chunk_size))
            if end_index > len(composite_key_list):
                end_index = len(composite_key_list)
            print('processing chunk ' + str(chunk) + ' with start index ' + str(start_index) + ' and end index ' + str(
                end_index))
            for each in self._db_model.query.filter(model_composite_key.in_(composite_key_list[start_index:end_index])):
                # use composite key to reference records on the items dict
                composite_key = ''
                for pk in self._primary_keys:
                    composite_key += str(getattr(each, pk))
                self._db_session.merge(items.pop(composite_key))
                update_cnt += 1

        self._db_session.add_all(items.values())
        logger.info('updating existing records: ' + str(update_cnt))
        logger.info('inserting new records: ' + str(len(items)))
        self._db_session.commit()


class MongoDataLoader(object):
    def __init__(self, collection, primary_keys):

        self._collection = collection
        self._primary_keys = primary_keys

    def load_to_db(self, data):

        if isinstance(data, list):
            for item in data:
                r = self._upsert_item(item)
                logger.info(str(r.raw_result))
        else:
            r = self._upsert_item(data)
            logger.info(str(r.raw_result))

    def _upsert_item(self, item):
        find_criteria = dict()
        for pk in self._primary_keys:
            find_criteria[pk] = item[pk]
        return self._collection.replace_one(find_criteria, item, upsert=True)

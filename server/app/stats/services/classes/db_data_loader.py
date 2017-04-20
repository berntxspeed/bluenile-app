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

    def load_to_db(self, item_generator, **kwargs):

        """
            primary_keys should be a list of strings of primary key field name to search for
            items should be a dict where key=str(primary key) value and value is the model instance
        """

        for last_batch, items in item_generator(**kwargs):

            update_cnt = 0  # keep track of updated records

            # build sqlalchemy composite key expression for use in finding pre-existing records
            model_composite_key = getattr(self._db_model, self._primary_keys[0])
            for pk in self._primary_keys[1:]:
                model_composite_key = model_composite_key.concat(getattr(self._db_model, pk))

            composite_key_list = list(items.keys())
            if len(composite_key_list) > 0:
                for each in self._db_model.query.filter(model_composite_key.in_(composite_key_list)):
                    # use composite key to reference records on the items dict
                    composite_key = ''
                    for pk in self._primary_keys:
                        composite_key += str(getattr(each, pk))
                    inst_to_update = items.pop(composite_key, None)
                    if inst_to_update is not None:
                        inst_to_update.id = each.id
                        self._db_session.merge(inst_to_update)
                        update_cnt += 1
                    else:
                        print('item not found: '+composite_key)

                print('updating existing records: ' + str(update_cnt))
                print('inserting new records: ' + str(len(items)))
                self._db_session.add_all(items.values())

                if last_batch:
                    print('done loading records')
                    self._db_session.commit()
                    break
            else:  # no records to update
                return

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

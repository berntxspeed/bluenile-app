import datetime
from ...stats.services.classes.db_data_loader import MongoDataLoader


class MongoTaskLoader(object):
    def __init__(self, client_instance, user_config=None):
        self._db = client_instance
        self._primary_key = 'task_id'
        self._collection_name = 'celery_tasks'

        user_account = user_config and user_config.get('account_name')
        if user_account:
            self._collection_name = self._collection_name + '_' + user_account

        self._collection = self._db[self._collection_name]
        self._limit = 1000

    @staticmethod
    def convert_timedate(all_results):
        for a_query in all_results:
            if a_query.get('timestamp'):
                a_query['timestamp'] = str(a_query['timestamp']).replace('T', ' at ')[:-5]

    def get_all_tasks(self):
        all_tasks = []
        try:
            for a_task in self._collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(self._limit):
                all_tasks.append(a_task)

            self.convert_timedate(all_tasks)
            return True, all_tasks
        except Exception as e:
            return False, 'Get All Tasks Failed: {0}'.format(str(e))

    def save_task(self, task):
        task['timestamp'] = datetime.datetime.utcnow().isoformat()
        item_loader = MongoDataLoader(self._collection, [self._primary_key])
        try:
            item_loader.load_to_db(task)
            return True, True
        except Exception as e:
            return False, 'Saving Task Failed: {0}'.format(str(e))

    def get_tasks_by_type(self, task_type):
        try:
            tasks = self._collection.find({ 'task_type': task_type } , { '_id': 0 }).sort('timestamp', -1).limit(self._limit)
            return True, tasks
        except Exception as e:
            return False, 'Getting Tasks Failed: {0}'.format(str(e))
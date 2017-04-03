from manage import celery, injector, app
from celery.schedules import crontab
from .injector_keys import DataLoadServ
from ...app.injector_keys import MongoDB



class BaseTask(celery.Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from celery import states
        """Log the exceptions to sentry."""
        # self.update_state(state='FAILURE',
        #                   meta={'The task failed. Please contact customer support for more information'})
        super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        task = {'status': status,
                'task_id': task_id,
                'retval': str(retval),
                'task_type': kwargs['task_type'],
                'einfo': str(einfo)
                }

        with app.app_context():
            mongo = injector.get(MongoDB)
            from server.app.task_admin.services.mongo_task_loader import MongoTaskLoader
            success, error = MongoTaskLoader(mongo.db).save_task(task)

        super(BaseTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


celery.conf.beat_schedule = {
    'every-4-hours_purchases': {
        'task': 'server.app.stats.workers.load_purchases',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'purchases'}
    },
    'every-4-hours_customers': {
        'task': 'server.app.stats.workers.load_customers',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'customers'}
    },
    'every-4-hours_web_tracking': {
        'task': 'server.app.stats.workers.load_web_tracking',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'web-tracking'}
    },
    'every-4-hours_mc_journeys': {
        'task': 'server.app.stats.workers.load_mc_journeys',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'mc-journeys'}
    },
    'every-4-hours_mc_email_data': {
        'task': 'server.app.stats.workers.load_mc_email_data',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'mc-email-data'}
    },
    'every-day_periodic_sync_to_mc': {
        'task': 'server.app.stats.workers.periodic_sync_to_mc',
        'schedule': crontab(minute=0, hour=0),
        'kwargs': {'task_type': 'periodic-sync'}
    }
}

@celery.task(base=BaseTask)
def load_customers(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_customers()


@celery.task(base=BaseTask)
def load_purchases(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_purchases()


@celery.task(base=BaseTask)
def load_mc_email_data(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_mc_email_data()


@celery.task
def load_artists():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_artists()


@celery.task(base=BaseTask)
def load_mc_journeys(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_mc_journeys()


@celery.task(base=BaseTask)
def load_web_tracking(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_web_tracking()


@celery.task
def add_fips_location_emlopen(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.add_fips_location_data('EmlOpen')


@celery.task
def add_fips_location_emlclick(**kwargs):
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.add_fips_location_data('EmlClick')


@celery.task(base=BaseTask)
def periodic_sync_to_mc(**kwargs):
    from server.app.data_builder.services.data_builder_query import DataBuilderQuery
    from .services.classes.stats_utils import find_relevant_periodic_tasks

    with app.app_context():
        mongo = injector.get(MongoDB)
        status, all_queries = DataBuilderQuery(mongo.db).get_all_queries()
        relevant_queries = find_relevant_periodic_tasks(all_queries)

        if len(relevant_queries):
            from ..data.workers import sync_query_to_mc
            for a_query in relevant_queries:
                sync_query_to_mc.delay(a_query, task_type='data-push')

NUM_OBJ_TO_CREATE = 30;


@celery.task(bind=True)
def long_task(self):
    # from server.app.injector_keys import SQLAlchemy
    # db = injector.get(SQLAlchemy)
    for i in range(1, NUM_OBJ_TO_CREATE + 1):
        # from server.app.common.models import User
        # user = User(fn, ln)

        # db.session.add(user)

        process_percent = int(100 * float(i) / float(NUM_OBJ_TO_CREATE))

        from time import sleep
        sleep(1)
        self.update_state(state='PROGRESS',
                          meta={'process_percent': process_percent})
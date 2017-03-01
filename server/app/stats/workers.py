from manage import celery, injector, app
from .injector_keys import DataLoadServ


class BaseTask(celery.Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from celery import states
        """Log the exceptions to sentry."""
        self.update_state(state='FAILURE',
                          meta={'The task failed. Please contact customer support for more information'})
        super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@celery.task(base=BaseTask)
def load_customers():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_customers()


@celery.task
def load_purchases():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_purchases()


@celery.task
def load_mc_email_data():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_mc_email_data()


@celery.task
def load_artists():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_artists()


@celery.task
def load_mc_journeys():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_mc_journeys()


@celery.task
def load_web_tracking():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_web_tracking()


@celery.task
def add_fips_location_emlopen():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.add_fips_location_data('EmlOpen')


@celery.task
def add_fips_location_emlclick():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.add_fips_location_data('EmlClick')


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


from celery.task.schedules import crontab
from celery.decorators import periodic_task

@periodic_task(run_every=(crontab(hour='*/4')), name="load_customers", ignore_result=True)
def load_customers_periodic():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_customers()

@periodic_task(run_every=(crontab(hour='*/4')), name="load_purchases", ignore_result=True)
def load_purchases_periodic():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_purchases()

@periodic_task(run_every=(crontab(hour='*/4')), name="load_web_tracking", ignore_result=True)
def load_web_tracking_periodic():
    with app.app_context():
        service = injector.get(DataLoadServ)
        service.load_web_tracking()
from manage import celery, injector, app
from .injector_keys import DataLoadServ


@celery.task
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


NUM_OBJ_TO_CREATE = 100;


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

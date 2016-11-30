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

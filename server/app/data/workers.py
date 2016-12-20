from manage import celery, injector, app
from .injector_keys import DataPushServ

@celery.task
def sync_data_to_mc(table):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.sync_data_to_mc(table)


@celery.task
def clean_sync_flags(table):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.clean_sync_flags(table)


from manage import celery, injector, app
from .injector_keys import DataPushServ

@celery.task
def sync_mc_data(table):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.sync_data_to_mc(table)


@celery.task
def clean_sync_flags(table):
    service = injector.get(DataPushServ)
    service.clr_ext_sync_flags(table)


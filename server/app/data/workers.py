from manage import celery, injector, app
from server.app.stats.workers import BaseTask
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


@celery.task(base=BaseTask)
def sync_query_to_mc(query_rules, **kwargs):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.sync_query_to_mc(query_rules)

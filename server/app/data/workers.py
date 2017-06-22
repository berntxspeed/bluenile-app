from manage import celery, injector, app
from server.app.stats.workers import BaseTask
from .injector_keys import DataPushServ


@celery.task(base=BaseTask)
def sync_data_to_mc(table, **kwargs):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.exec_safe_session(service.sync_data_to_mc, table)


@celery.task
def clean_sync_flags(table):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.exec_safe_session(service.clean_sync_flags, table)


@celery.task(base=BaseTask)
def sync_query_to_mc(query_rules, **kwargs):
    with app.app_context():
        service = injector.get(DataPushServ)
        service.exec_safe_session(service.sync_query_to_mc, query_rules)

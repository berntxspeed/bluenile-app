from manage import celery, injector, app
from server.app.stats.workers import BaseTask
from .injector_keys import DataPushServ, UserDataPushServ


@celery.task(base=BaseTask)
def sync_data_to_mc(table, **kwargs):
    # TODO: remove if/else to default to user_db
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataPushServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.sync_data_to_mc, table)
    else:
        with app.app_context():
            service = injector.get(DataPushServ)
            service.exec_safe_session(service.sync_data_to_mc, table)


@celery.task
def clean_sync_flags(table, **kwargs):
    # TODO: remove if/else to default to user_db
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataPushServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.clean_sync_flags, table)
    else:
        with app.app_context():
            service = injector.get(DataPushServ)
            service.exec_safe_session(service.clean_sync_flags, table)


@celery.task(base=BaseTask)
def sync_query_to_mc(query_rules, **kwargs):
    # TODO: remove if/else to default to user_db
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataPushServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.sync_query_to_mc, query_rules)
    else:
        with app.app_context():
            service = injector.get(DataPushServ)
            service.exec_safe_session(service.sync_query_to_mc, query_rules)

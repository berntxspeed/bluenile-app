from time import sleep
from manage import celery, injector, app
from celery.schedules import crontab
from .injector_keys import UserDataLoadServ
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
                'task_type': kwargs.get('task_type'),
                'einfo': str(einfo)
                }
        with app.app_context():
            mongo = injector.get(MongoDB)
            from server.app.task_admin.services.mongo_task_loader import MongoTaskLoader
            success, error = MongoTaskLoader(mongo.db, kwargs.get('user_params')).save_task(task)

            if kwargs.get('task_type') == 'data-push':
                if kwargs.get('query_name') is not None:
                    from server.app.data_builder.services.data_builder_query import DataBuilderQuery
                    status, result = DataBuilderQuery(mongo.db, kwargs.get('user_params')).update_last_run_info(kwargs['query_name'])
                if kwargs.get('remaining_queries') is not None:
                    rem_queries = kwargs['remaining_queries']
                    if len(rem_queries) > 0:
                        from ..data.workers import sync_query_to_mc
                        a_query = rem_queries.pop()
                        sync_query_to_mc.delay(a_query,
                                               task_type='data-push',
                                               query_name=a_query.get('name'),
                                               remaining_queries=rem_queries,
                                               user_params=kwargs.get('user_params'))

            elif kwargs.get('task_type', '').startswith('load'):
                from server.app.stats.services.mongo_user_config_loader import MongoDataJobConfigLoader
                _, result = MongoDataJobConfigLoader(mongo.db, kwargs.get('user_params')).update_last_load_info(kwargs['task_type'])

                # schedule sync_query_to_mc for all queries after successful data load
                if status == 'SUCCESS' and kwargs.get('sync_queries') is True:
                    sync_all_queries_to_mc.delay(task_type='sync-all-queries', user_params=kwargs.get('user_params'))

        super(BaseTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


celery.conf.beat_schedule = {
    """
    'every-1-hours_lead_perfection': {
        'task': 'server.app.stats.workers.load_lead_perfection',
        'schedule': crontab(minute=0, hour='*/1'),
        'kwargs': {'task_type': 'lead_perfection'}
    },
    'every-4-hours_web_tracking': {
        'task': 'server.app.stats.workers.load_web_tracking',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'task_type': 'web-tracking'}
    },
    'every-hour_schedule_sync_jobs': {
        'task': 'server.app.stats.workers.schedule_sync_jobs',
        'schedule': crontab(minute=0, hour='*'),
        'kwargs': {'task_type': 'schedule-sync-jobs', 'user_params': {'account_name': 'bluenile'}}
    },
    'every-hour_schedule_load_jobs': {
        'task': 'server.app.stats.workers.schedule_load_jobs',
        'schedule': crontab(minute=30, hour='*'),
        'kwargs': {'task_type': 'schedule-load-jobs', 'user_params': {'account_name': 'bluenile'}}
    }
    """
    'every-4-hours_mc_journeys': {
        'task': 'server.app.stats.workers.load_mc_journeys',
        'schedule': crontab(minute='0,10,20,30,40,50', hour='*'),
        'kwargs': {'task_type': 'mc-journeys', 'user_params': {'account_name': 'Galileo', 'postgres_uri': 'irrelevant'}}
    },
    'every-4-hours_mc_email_data': {
        'task': 'server.app.stats.workers.load_mc_email_data',
        'schedule': crontab(minute='0,10,20,30,40,50', hour='*'),
        'kwargs': {'task_type': 'mc-email-data', 'user_params': {'account_name': 'Galileo',
                                                                 'postgres_uri': 'postgresql://bluenilesw:BlueNileSW123!@postgres-dev.cdwkdjoq5xbu.us-east-2.rds.amazonaws.com:5432/galileo'}
                   }
    }
}


@celery.task(base=BaseTask)
def basic_load_task(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.simple_data_load, **kwargs)


@celery.task(base=BaseTask)
def load_mc_email_data(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.load_mc_email_data)


@celery.task(base=BaseTask)
def load_mc_journeys(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params, postgres_required=False)
            service.exec_safe_session(service.load_mc_journeys)


@celery.task(base=BaseTask)
def load_web_tracking(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.load_web_tracking)


@celery.task
def add_fips_location_emlopen(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.add_fips_location_data, 'EmlOpen')


@celery.task
def add_fips_location_emlclick(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.add_fips_location_data, 'EmlClick')


@celery.task(base=BaseTask)
def sync_all_queries_to_mc(**kwargs):
    with app.app_context():
        mongo = injector.get(MongoDB)
        from ..data_builder.services.data_builder_query import DataBuilderQuery

        user_params = kwargs.get('user_params')
        get_queries_status, all_queries = DataBuilderQuery(mongo.db, user_params).get_all_queries(type='auto_sync')
        if get_queries_status is True:
            from ..data.workers import sync_query_to_mc
            if len(all_queries):
                print('Found {0} Queries for Auto Sync:\n{1}'.
                      format(len(all_queries), ', '.join(q.get('name') for q in all_queries)))
                a_query = all_queries.pop()
                sync_query_to_mc.delay(a_query,
                                       task_type='data-push',
                                       query_name=a_query.get('name'),
                                       remaining_queries=all_queries,
                                       user_params=user_params)


@celery.task(base=BaseTask)
def schedule_sync_jobs(**kwargs):
    from server.app.data_builder.services.data_builder_query import DataBuilderQuery
    from .services.classes.stats_utils import find_relevant_periodic_tasks
    from server.app.common.models.system_models import ClientAccount, session_scope

    #Find all the active client accounts
    user_configs = []
    with session_scope() as session:
        client_accounts_result = session.query(ClientAccount).all()
        for an_account in client_accounts_result:
            print('account name: ', an_account.account_name)
            user_configs.append(dict(account_name=an_account.account_name, postgres_uri=an_account.database_uri))

    for a_user_config in user_configs:
        with app.app_context():
            mongo = injector.get(MongoDB)
            status, all_queries = DataBuilderQuery(mongo.db, a_user_config).get_all_queries()
            relevant_queries = find_relevant_periodic_tasks(all_queries)

            if len(relevant_queries):
                from ..data.workers import sync_query_to_mc
                for a_query in relevant_queries:
                    print('query name: ', a_query.get('name'))
                    sync_query_to_mc.delay(a_query, task_type='data-push', query_name=a_query.get('name'), user_params=a_user_config)


@celery.task(base=BaseTask)
def schedule_load_jobs(**kwargs):
    from server.app.stats.services.mongo_user_config_loader import MongoDataJobConfigLoader
    from .services.classes.stats_utils import find_relevant_periodic_tasks
    from server.app.common.models.system_models import ClientAccount, session_scope

    #Find all the active client accounts
    user_configs = []
    with session_scope() as session:
        client_accounts_result = session.query(ClientAccount).all()
        for an_account in client_accounts_result:
            print('account name: ', an_account.account_name)
            user_configs.append(dict(account_name=an_account.account_name, postgres_uri=an_account.database_uri))

    for a_user_config in user_configs:
        print ('user_config', a_user_config)
        with app.app_context():
            mongo = injector.get(MongoDB)
            status, dl_jobs = MongoDataJobConfigLoader(mongo.db, a_user_config).get_data_load_jobs()
            relevant_load_jobs = find_relevant_periodic_tasks(dl_jobs)

            if len(relevant_load_jobs):
                    from .workers import basic_load_task, load_mc_journeys, \
                        load_web_tracking, load_lead_perfection
                    from .workers import add_fips_location_emlopen, add_fips_location_emlclick
                    from ..data.workers import sync_data_to_mc

                    load_map = {'x2crm_customers': {'load_func': basic_load_task,
                                                    'data_source': 'x2crm',
                                                    'data_type': 'customer'},
                                'zoho_customers': {'load_func': basic_load_task,
                                                   'data_source': 'zoho',
                                                   'data_type': 'customer'},
                                'magento_customers': {'load_func': basic_load_task,
                                                      'data_source': 'magento',
                                                      'data_type': 'customer'},
                                'magento_purchases': {'load_func': basic_load_task,
                                                      'data_source': 'magento',
                                                      'data_type': 'purchase'},
                                'shopify_customers': {'load_func': basic_load_task,
                                                      'data_source': 'shopify',
                                                      'data_type': 'customer'},
                                'shopify_purchases': {'load_func': basic_load_task,
                                                      'data_source': 'shopify',
                                                      'data_type': 'purchase'},
                                'bigcommerce_customers': {'load_func': basic_load_task,
                                                          'data_source': 'bigcommerce',
                                                          'data_type': 'customer'},
                                'bigcommerce_purchases': {'load_func': basic_load_task,
                                                          'data_source': 'bigcommerce',
                                                          'data_type': 'purchase'},
                                'stripe_customers': {'load_func': basic_load_task,
                                                     'data_source': 'stripe',
                                                     'data_type': 'customer'},
                                # 'artists': load_artists,
                                'mc-email-data': load_mc_email_data,
                                'mc-journeys': load_mc_journeys,
                                'web-tracking': load_web_tracking,
                                'add-fips-location-emlopen': add_fips_location_emlopen,
                                'add-fips-location-emlclick': add_fips_location_emlclick,
                                'lead-perfection': load_lead_perfection,
                                'customer_table': {'load_func': sync_data_to_mc,
                                                   'table_name': 'customer',
                                                   },
                                'purchase_table': {'load_func': sync_data_to_mc,
                                                   'table_name': 'purchase',
                                                   }
                                }

                    while len(relevant_load_jobs):
                        a_job = relevant_load_jobs.pop()
                        task = load_map.get(a_job.get('job_type'))
                        if not task:
                            continue
                        sync_queries = (len(relevant_load_jobs) == 0)
                        if 'table_name' in task:
                            task['load_func'].delay(task['table_name'],
                                                    task_type='load_' + a_job['job_type'],
                                                    table_name=task['table_name'],
                                                    user_params=a_user_config)
                        else:
                            task['load_func'].delay(task_type='load_' + a_job['job_type'],
                                                    data_source=task['data_source'],
                                                    data_type=task['data_type'],
                                                    sync_queries=sync_queries,
                                                    user_params=a_user_config)

                        sleep(60)


@celery.task(base=BaseTask)
def load_lead_perfection(**kwargs):
    user_params = kwargs.get('user_params')
    if user_params:
        with app.app_context():
            service = injector.get(UserDataLoadServ)
            service.init_user_db(user_params)
            service.exec_safe_session(service.load_lead_perfection)


NUM_OBJ_TO_CREATE = 30


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


from json import dumps, loads

from flask import Response, Request
from flask import request, redirect
from flask import session
from flask_login import login_required
from injector import inject

from . import stats
from .injector_keys import JbStatsServ, GetStatsServ
from .services.mongo_user_config_loader import MongoUserApiConfigLoader, MongoDataJobConfigLoader
from server.app.injector_keys import MongoDB, UserSessionConfig
from ..common.views.decorators import templated
from ..data_builder.services.query_service import SqlQueryService


# Pass this function to require login for every request
@stats.before_request
@login_required
def before_request():
    pass


@stats.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@stats.route('/special-logged-in-page')
@inject(jb_stats_service=JbStatsServ)
@templated('special_logged_in_page')
def special_logged_in_page(jb_stats_service):
    return jb_stats_service.special_logged_in_page(request=request, session=session)


@stats.route('/data-manager')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
@templated('data_manager')
def data_manager(mongo, user_config):
    user = dict(account=session.get('user_params', {}).get('account_name'))
    status, avail_vendors = MongoUserApiConfigLoader(mongo.db, user_config).get_user_api_config()
    return {'status': status, 'avail_vendors': avail_vendors, 'user': user}


@stats.route('/data-manager/save-load-job-config/', methods=['POST'])
@inject(mongo=MongoDB, user_config=UserSessionConfig)
def save_load_job_config(mongo, user_config):
    load_job_config = request.json
    success, error = MongoDataJobConfigLoader(mongo.db, user_config).save_data_load_config(load_job_config)
    if success:
        return 'OK', 200
    else:
        return error, 500


@stats.route('/data-manager/get-data-sources')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
def get_data_sources(mongo, user_config):

    status, data_load_jobs = MongoUserApiConfigLoader(mongo.db, user_config).get_user_api_config()
    columns = [{
            'field': 'data_source',
            'title': 'Data Source'
        },
        {
            'field': 'domain',
            'title': 'Domain'
        }]
    return Response(dumps({'columns': columns, 'data': data_load_jobs}, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')


@stats.route('/data-manager/delete-api-config/<data_source>', methods=['POST'])
@inject(mongo=MongoDB, user_config=UserSessionConfig)
def delete_vendor_api_config(mongo, user_config, data_source):
    success, error = MongoUserApiConfigLoader(mongo.db, user_config).remove_api_config_by_source(data_source)
    if success:
        return 'OK', 200
    else:
        return error, 500


@stats.route('/data-manager/save-api-config', methods=['POST'])
@inject(mongo=MongoDB, user_config=UserSessionConfig)
def save_vendor_api_config(mongo, user_config):
    vendor_config = request.json
    success, error = MongoUserApiConfigLoader(mongo.db, user_config).save_api_config(vendor_config)
    if success:
        return 'OK', 200
    else:
        return error, 500


@stats.route('/data-manager/get-dl-jobs')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
def get_data_load_jobs(mongo, user_config):

    status, data_load_jobs = MongoDataJobConfigLoader(mongo.db, user_config).get_data_load_jobs()
    columns = [{
                    'field': 'job_type_full',
                    'title': 'Data Load Type'
                },
                {
                    'field': 'frequency',
                    'title': 'Frequency'
                },
                {
                    'field': 'last_run',
                    'title': 'Last Load'
                }]
    return Response(dumps({'columns': columns, 'data': data_load_jobs}, default=SqlQueryService.alchemy_encoder),
                    mimetype='application/json')


@stats.route('/journey-view')
@inject(jb_stats_service=JbStatsServ)
@templated('journey_view')
def journey_view(jb_stats_service):
    # passes all journey ids to view
    return jb_stats_service.journey_view()


@stats.route('/journey-detail/<id>')
@inject(jb_stats_service=JbStatsServ)
def journey_detail(jb_stats_service, id):
    # returns all information about one journey
    result = jb_stats_service.journey_detail(id)
    return Response(dumps(result), mimetype='application/json')


@stats.route('/report-view')
@inject(get_stats_service=GetStatsServ)
@templated('report_view')
def report_view(get_stats_service):
    # passes all send ids to view
    return get_stats_service.report_view()


@stats.route('/send-info/<option>', methods=['POST'])
@inject(request=Request, get_stats_service=GetStatsServ)
def send_info(request, get_stats_service, option):
    # sends info about a single email send
    return get_stats_service.send_info(option, request)


@stats.route('/celery-task-test')
@templated('celery_updater')
def sample_long_task():
    from server.app.stats.workers import long_task
    task = long_task.delay()
    print(task.backend)
    return dict(task_id=task.id)


@stats.route('/task_update')
def check_tasks_status():
    # from server.app.stats.workers import long_task
    from manage import celery

    task_id = request.args.get('task_id')
    task = celery.AsyncResult(task_id)
    data = {'state': task.state,
            'result': task.result if task.result is Exception else str(task.result)}
    return Response(dumps(data), mimetype='application/json')


@stats.route('/devpage-joint')
@templated('devpage_joint')
def devpage_joint():
    return {}


@stats.route('/load/<action>')
@templated('data_manager')
def load(action):
    from .workers import basic_load_task, load_mc_email_data, load_mc_journeys, \
                         load_web_tracking, load_lead_perfection
    from .workers import add_fips_location_emlopen, add_fips_location_emlclick
    from ..data.workers import sync_data_to_mc

    user = dict(account=session.get('user_params', {}).get('account_name'))
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
                                    },
                }

    task = load_map.get(action, None)
    if task is None:
        return Exception('No such action is available')

    user_params = session.get('user_params')

    if isinstance(task, dict):
        if 'table_name' in task:
            result = task['load_func'].delay(task['table_name'],
                                             task_type='load_'+action,
                                             table_name=task['table_name'],
                                             user_params=user_params)
        else:
            result = task['load_func'].delay(task_type='load_'+action,
                                             data_source=task['data_source'],
                                             data_type=task['data_type'],
                                             sync_queries=True,
                                             user_params=user_params)
    else:
        result = task.delay(task_type=action)

    return dict(task_id=result.id, user=user)


@stats.route('/get-columns/<tbl>')
@inject(get_stats_service=GetStatsServ)
def get_columns(get_stats_service, tbl):
    return get_stats_service.get_columns(tbl)


@stats.route('/metrics-grouped-by/<tbl>/<grp_by>/<agg_op>/<agg_field>', methods=['GET', 'POST'])
@inject(get_stats_service=GetStatsServ)
def metrics_grouped_by(get_stats_service, tbl, grp_by, agg_op, agg_field):
    """
    tbl = 'EmlOpen' # a table to query
    grp_by = 'Device' # a db field name to group by
        if multiple group bys are required = 'OperatingSystem-Device'
    filters=[
        {
            'field': 'EventDate',
            'op': 'gt',
            'val': '12/01/2016 11:59:00 PM'
        },{
            'field': 'EventDate',
            'op': 'lt',
            'val': '11/01/2016 11:59:00 PM'
        },{
            'field': 'SendID',
            'op': 'eq',
            'val': '23421'
        }
    ]
    """
    if grp_by is None:
        return Exception('Must provide a column to group by')
    filters = None
    if request.method == 'GET':
        q = request.args.get('q', None)
    else:
        q = request.form.get('q', None)
    if q:
        q = loads(q)
        filters = q.get('filters')
        print(filters)
    if agg_field == 'none':
        agg_field = None
    return get_stats_service.get_grouping_counts(tbl, grp_by, agg_op, agg_field, filters)


@stats.route('/map-graph')
@templated('map_graph')
def map_graph():
    return {}


@stats.route('/save-report/<rpt_id>/<rpt_name>/<graph_type>/<tbl>/<grp_by>/<agg_op>/<agg_field>', methods=['GET', 'POST'])
@inject(get_stats_service=GetStatsServ)
def save_report(get_stats_service, rpt_id, rpt_name, graph_type, tbl, grp_by, agg_op, agg_field):
    if rpt_id == 'null':
        rpt_id = None
    filters = None
    if request.method == 'GET':
        q = request.args.get('q', None)
    else:
        q = request.form.get('q', None)
    if q:
        q = loads(q)
        filters = q.get('filters')
        print(filters)
    if agg_field == 'none':
        agg_field = None
    return get_stats_service.save_report(rpt_id, rpt_name, graph_type, tbl, grp_by, agg_op, agg_field, filters)


@stats.route('/report/<rpt_id>')
@inject(get_stats_service=GetStatsServ)
def report(get_stats_service, rpt_id):
    return get_stats_service.get_report(rpt_id)


@stats.route('/delete-report/<rpt_id>')
@inject(get_stats_service=GetStatsServ)
def delete_report(get_stats_service, rpt_id):
    return get_stats_service.delete_report(rpt_id)

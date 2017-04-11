from json import dumps, loads

from flask import Response
from flask import request
from flask import session
from flask_login import login_required
from injector import inject

from . import stats
from .injector_keys import JbStatsServ, GetStatsServ
from ..common.views.decorators import templated


# Pass this function to require login for every request
@stats.before_request
@login_required
def before_request():
    pass


@stats.route('/special-logged-in-page')
@inject(jb_stats_service=JbStatsServ)
@templated('special_logged_in_page')
def special_logged_in_page(jb_stats_service):
    return jb_stats_service.special_logged_in_page(request=request, session=session)


@stats.route('/data-manager')
@templated('data_manager')
def data_manager():
    return {}

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

@stats.route('/send-info/<option>/<sendid>')
@inject(get_stats_service=GetStatsServ)
def send_info(get_stats_service, option, sendid):
    # sends info about a single email send
    return get_stats_service.send_info(option, sendid)


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
    from .workers import load_customers, load_artists, load_mc_email_data, load_mc_journeys, load_purchases, \
        load_web_tracking, load_lead_perfection
    from .workers import add_fips_location_emlopen, add_fips_location_emlclick

    load_map = {'customers': load_customers,
                'purchases': load_purchases,
                'artists': load_artists,
                'mc-email-data': load_mc_email_data,
                'mc-journeys': load_mc_journeys,
                'web-tracking': load_web_tracking,
                'add-fips-location-emlopen': add_fips_location_emlopen,
                'add-fips-location-emlclick': add_fips_location_emlclick,
                'lead-perfection': load_lead_perfection}
    task = load_map.get(action, None)
    if task is None:
        return Exception('No such action is available')
    result = task.delay(task_type=action)
    return dict(task_id=result.id)


@stats.route('/get-columns/<tbl>')
@inject(get_stats_service=GetStatsServ)
def get_columns(get_stats_service, tbl):
    return get_stats_service.get_columns(tbl)


@stats.route('/metrics-grouped-by/<tbl>/<grp_by>/<agg_op>/<agg_field>')
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
    q = request.args.get('q')
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

@stats.route('/save-report/<rpt_id>/<rpt_name>/<graph_type>/<tbl>/<grp_by>/<agg_op>/<agg_field>')
@inject(get_stats_service=GetStatsServ)
def save_report(get_stats_service, rpt_id, rpt_name, graph_type, tbl, grp_by, agg_op, agg_field):
    if rpt_id == 'null':
        rpt_id = None
    filters = None
    q = request.args.get('q')
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

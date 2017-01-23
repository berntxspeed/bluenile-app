from flask import request
from flask import session
from flask import Response
from flask_login import login_required
from injector import inject
from json import dumps, loads

from sqlalchemy import Integer

from server.app.common.models import *
from server.app.injector_keys import SQLAlchemy
from sqlalchemy import inspect
from . import stats
from .injector_keys import JbStatsServ, GetStatsServ, DataLoadServ
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


def type_mapper(type):
    if (type.python_type is datetime) or isinstance(type, TIMESTAMP):
        return 'datetime'
    if (type.python_type is int) or isinstance(type, Integer):
        return 'integer'
    if type.python_type is float:
        return 'double'
    if type.python_type is bool:
        return 'boolean'
    return 'string'


@stats.route('/data-builder')
@inject(db=SQLAlchemy)
@templated('data_builder')
def data_builder(db):
    result = dict()

    for model in [Customer, EmlOpen, EmlSend, EmlClick, Purchase, WebTrackingEvent,
                  WebTrackingEcomm, WebTrackingPageView, Artist]:
        columns = inspect(model).columns
        field_dict = dict()
        for column in columns:
            field_dict[column.key] = {
                'key': column.key,
                'name': column.name,
                'table': model.__name__,
                'expression': model.__name__ + '.' + column.name,
                'type': type_mapper(column.type)
            }

        result[model.__name__] = field_dict

    return {
        'tables':
            {
                'users': {
                    'fields': ['username', 'nickname', 'email']
                },
                'eml_open': {
                    'fields': ['SendId', 'SubscriberKey', 'EmailAddress']
                },
                'eml_click': {
                    'fields': ['City', 'Country', 'Region', 'URL', 'Alias', 'Browser', 'Device']
                },
                'eml_send': {},
                'purchase': {},
                'web_event': {},
                'customer': {},
                'web_tracking_event': {},
                'web_tracking_page_view': {},
                'artist': {}
            }
    }


@stats.route('/build-tables')
@inject(db=SQLAlchemy)
def table_builder(db):
    result = {
        'tables': {
            'users': {'selected': True},
            'eml_open': {'selected': True},
            'eml_click': {'selected': True}
        },
        'rules': {
            'condition': 'AND',
            'rules': [
                {
                    'id': 'users.username',
                    'operator': 'equal',
                    'value': "Bernt"
                }, {
                    'condition': 'OR',
                    'rules': [
                        {
                            'id': 'eml_open.EmailAddress',
                            'operator': 'equal',
                            'value': "bernt@bluenilesw.com"
                        }, {
                            'id': 'eml_click.City',
                            'operator': 'equal',
                            'value': "San Francisco"
                        }
                    ]
                }
            ]
        }
    }
    return Response(dumps(result), mimetype='application/json')


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
        load_web_tracking
    from .workers import add_fips_location_emlopen, add_fips_location_emlclick

    load_map = {'customers': load_customers,
                'purchases': load_purchases,
                'artists': load_artists,
                'mc-email-data': load_mc_email_data,
                'mc-journeys': load_mc_journeys,
                'web-tracking': load_web_tracking,
                'add-fips-location-emlopen': add_fips_location_emlopen,
                'add-fips-location-emlclick': add_fips_location_emlclick}
    task = load_map.get(action, None)
    if task is None:
        return Exception('No such action is available')
    result = task.delay()
    return dict(task_id=result.id)


@stats.route('/get-columns/<tbl>')
@inject(get_stats_service=GetStatsServ)
def get_columns(get_stats_service, tbl):
    return get_stats_service.get_columns(tbl)


@stats.route('/metrics-grouped-by/<grp_by>/<tbl>')
@inject(get_stats_service=GetStatsServ)
def metrics_grouped_by(get_stats_service, grp_by, tbl):
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
    return get_stats_service.get_grouping_counts(tbl, grp_by, filters)


@stats.route('/map-graph')
@templated('map_graph')
def map_graph():
    return {}

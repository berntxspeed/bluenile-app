from flask import request
from flask import session
from flask import Response
from flask import url_for
from flask_login import login_required
from injector import inject
from json import dumps, loads

from werkzeug.utils import redirect

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


@stats.route('/devpage-joint')
@templated('devpage_joint')
def devpage_joint():
    return {}


# todo collapse into one endpoint, parametrize destination table
@stats.route('/load/customers')
def load_customers():
    from .workers import load_customers
    result = load_customers.delay()
    return Response(dumps(dict(taskId=result.id)), mimetype='application/json')


@stats.route('/load/artists')
def load_artists():
    from .workers import load_artists
    result = load_artists.delay()
    return Response(dumps(dict(taskId=result.id)), mimetype='application/json')


@stats.route('/load/mc-email-data')
def load_mc_email_data():
    from .workers import load_mc_email_data
    result = load_mc_email_data.delay()
    print('worker task: load_mc_email_data: id: ' + result.id)
    return Response(dumps(dict(taskId=result.id)), mimetype='application/json')


@stats.route('/load/mc-journeys')
def load_mc_journeys():
    from .workers import load_mc_journeys
    result = load_mc_journeys.delay()
    return Response(dumps(dict(taskId=result.id)), mimetype='application/json')


@stats.route('/get-columns/<tbl>')
@inject(get_stats_service=GetStatsServ)
def get_columns(get_stats_service, tbl):
    return get_stats_service.get_columns(tbl)


@stats.route('/metrics-grouped-by/<grp_by>/<tbl>')
@inject(get_stats_service=GetStatsServ)
def metrics_grouped_by(get_stats_service, grp_by, tbl):
    filters = None
    q = request.args.get('q')
    if q:
        q = loads(q)
        filters = q.get('filters')
        print(filters)
    return get_stats_service.get_grouping_counts(tbl, grp_by, filters)

from flask import request
from flask import session
from flask import Response
from flask_login import login_required
from injector import inject
from json import dumps, loads

from . import stats
from .injector_keys import JbStatsServ, GetStatsServ, DataLoadServ
from ..common.views.decorators import templated


@stats.route('/special-logged-in-page')
@inject(jb_stats_service=JbStatsServ)
@login_required
@templated('special_logged_in_page')
def special_logged_in_page(jb_stats_service):
    return jb_stats_service.special_logged_in_page(request=request, session=session)

@stats.route('/data-manager')
@login_required
@templated('data_manager')
def data_manager():
    return {}

@stats.route('/journey-view')
@inject(jb_stats_service=JbStatsServ)
@login_required
@templated('journey_view')
def journey_view(jb_stats_service):
    # passes all journey ids to view
    return jb_stats_service.journey_view()

@stats.route('/journey-detail/<id>')
@inject(jb_stats_service=JbStatsServ)
@login_required
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
@inject(data_load_service=DataLoadServ)
@login_required
def load_customers(data_load_service):
    return data_load_service.load_customers()

@stats.route('/load/artists')
@inject(data_load_service=DataLoadServ)
@login_required
def load_artists(data_load_service):
    return data_load_service.load_artists()

@stats.route('/load/mc-email-data')
@inject(data_load_service=DataLoadServ)
@login_required
def load_mc_email_data(data_load_service):
    return data_load_service.load_mc_email_data()

@stats.route('/load/mc-journeys')
@inject(data_load_service=DataLoadServ)
@login_required
def load_mc_journeys(data_load_service):
    return data_load_service.load_mc_journeys()

@stats.route('/get-columns/<tbl>')
@inject(get_stats_service=GetStatsServ)
@login_required
def get_columns(get_stats_service, tbl):
    return get_stats_service.get_columns(tbl)

@stats.route('/metrics-grouped-by/<grp_by>/<tbl>')
@inject(get_stats_service=GetStatsServ)
@login_required
def metrics_grouped_by(get_stats_service, grp_by, tbl):
    filters = None
    q = request.args.get('q')
    if q:
        q = loads(q)
        filters = q.get('filters')
        print(filters)
    return get_stats_service.get_grouping_counts(tbl, grp_by, filters)
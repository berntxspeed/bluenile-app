import celery
from flask import request
from flask import session
from flask import Response
from flask import url_for
from flask_login import login_required
from injector import inject
from json import dumps

from werkzeug.utils import redirect

from . import stats
from .injector_keys import JbStatsServ, DataLoadServ
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


@stats.route('/load/customers')
def load_customers():
    from ..common.workers.module import load_customers
    load_customers.delay()
    return redirect(url_for('stats.data_manager'))


@stats.route('/load/artists')
def load_artists():
    from ..common.workers.module import load_artists
    load_artists.delay()
    return redirect(url_for('stats.data_manager'))


@stats.route('/load/mc-email-data')
def load_mc_email_data():
    from ..common.workers.module import load_mc_email_data
    load_mc_email_data.delay()
    return redirect(url_for('stats.data_manager'))


@stats.route('/load/mc-journeys')
def load_mc_journeys():
    from ..common.workers.module import load_mc_journeys
    load_mc_journeys.delay()
    return redirect(url_for('stats.data_manager'))

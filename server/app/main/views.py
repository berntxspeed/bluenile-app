from flask import request, redirect
from flask_login import login_required

from ..common.views import context_processors
from . import main
from ..common.views.decorators import templated


@main.before_request
@login_required
def before_request():
    pass

@main.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@main.route('/')
@main.route('/index')
@templated('index')
def index():
    user = {'nickname': 'Bernt'} # fake user
    return dict(user=user)


from flask import request, redirect
from flask_login import login_required

from ..common.views import context_processors
from . import main
from ..common.views.decorators import templated


@main.route('/')
@main.route('/index')
@templated('index')
def index():
    user = {'nickname': 'Bernt'} # fake user
    return dict(user=user)


from flask import request, redirect, session
from flask_login import login_required

from ..common.views import context_processors
from . import main
from ..common.views.decorators import templated


@main.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@main.route('/')
@main.route('/index')
@login_required
@templated('index')
def index():
    user_name = session.get('user_name', 'Anonymous')
    user = {'nickname': user_name} # Okta User
    return dict(user=user)


from flask import abort
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from functools import wraps
from injector import inject

from . import auth
from .injector_keys import AuthServ
from ..common.views.decorators import templated


def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@auth.before_app_request
def csrf_protect():
    if request.method == 'POST':
        token = session.get('_csrf_token')
        if not token or token not in (request.form.get('csrf'), request.headers.get('X-CSRFToken')):
            abort(403)


@auth.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

"""
@auth.route('/facebook-authorized')
@logout_required
@inject(auth_service=AuthServ)
def facebook_authorized(auth_service):
    return auth_service.facebook_authorized(request=request, session=session)

@auth.route('/facebook-login')
@logout_required
@inject(auth_service=AuthServ)
def facebook_login(auth_service):
    return auth_service.facebook_login(request=request)

@auth.route('/facebook-signup', methods=['GET', 'POST'])
@logout_required
@inject(auth_service=AuthServ)
@templated('facebook_signup')
def facebook_signup(auth_service):
    return auth_service.facebook_signup(request=request, session=session)

@auth.route('/google-authorized')
@logout_required
@inject(auth_service=AuthServ)
def google_authorized(auth_service):
    return auth_service.google_authorized(request=request, session=session)

@auth.route('/google-login')
@logout_required
@inject(auth_service=AuthServ)
def google_login(auth_service):
    return auth_service.google_login(request=request)

@auth.route('/google-signup', methods=['GET', 'POST'])
@logout_required
@inject(auth_service=AuthServ)
@templated('google_signup')
def google_signup(auth_service):
    return auth_service.google_signup(request=request, session=session)
"""


@auth.route('/login', methods=['GET', 'POST'])
@logout_required
@inject(auth_service=AuthServ)
@templated('login')
def login(auth_service):
    return auth_service.login(request)


@auth.route('/logout')
@login_required
@inject(auth_service=AuthServ)
@templated('logout')
def logout(auth_service):
    return auth_service.logout()

"""
@auth.route('/signup', methods=['GET', 'POST'])
@logout_required
@inject(auth_service=AuthServ)
@templated('signup')
def signup(auth_service):
    return auth_service.signup(request)
"""
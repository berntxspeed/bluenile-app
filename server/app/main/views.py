from flask import request, redirect, session
from flask_login import login_required, current_user

from server.app.auth.services import AuthService
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
    user = current_user
    user_name = user.firstname #session.get('user_name', 'Anonymous')
    account = session['user_params']['account_name']
    accounts = AuthService.get_user_accounts(user.email)
    user = {'nickname': user_name,
            'account': account,
            'accounts': [acc.account_name for acc in accounts]} # Okta User
    return dict(user=user)

@main.route('/')
@main.route('/change-account/<new_account_name>')
@login_required
@templated('index')
def change(new_account_name):
    user = current_user
    accounts = AuthService.get_user_accounts(user.email)
    from server.app.common.models.system_models import ClientAccount
    new_account = accounts.filter(ClientAccount.account_name == new_account_name).first()
    AuthService.set_user_account(new_account)

    return index()
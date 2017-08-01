from flask import request, redirect, session
from flask_login import login_required, current_user

from . import main
from ..common.views.decorators import templated

from injector import inject
from ..auth.injector_keys import AuthServ


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
    user_name = user.firstname
    return_dict = {'nickname': user_name}
    return dict(user=return_dict)


@main.route('/')
@main.route('/change-account/<new_account_name>')
@login_required
@inject(auth_service=AuthServ)
@templated('index')
def change(auth_service, new_account_name):
    user = current_user
    accounts = auth_service.get_user_accounts(user.email)
    from server.app.common.models.system_models import ClientAccount
    new_account = accounts.filter(ClientAccount.account_name == new_account_name).first()

    #error checking
    if new_account is None:
        return redirect("/index")
    auth_service.set_user_account(new_account)

    return index()
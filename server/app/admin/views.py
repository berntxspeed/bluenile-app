import csv
import traceback
from io import StringIO

from json import dumps
from flask import Response
from flask import make_response
from flask import request, redirect, session
from flask_login import login_required, current_user
from injector import inject

from server.app.common.views.decorators import templated
from server.app.data_builder.services.query_service import SqlQueryService
from server.app.injector_keys import MongoDB, UserSessionConfig, Config
from server.app.admin.services.account_creation_service import AccountCreationService
from . import admin
from .services.mongo_task_loader import MongoTaskLoader
from ..auth.injector_keys import AuthServ


@admin.before_request
@login_required
def before_request():
    pass


@admin.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@admin.route('/admin-panel/')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
@templated('admin_panel')
def admin_panel(mongo, user_config):
    status, tasks = MongoTaskLoader(mongo.db, user_config).get_all_tasks()
    user = dict(account=session.get('user_params', {}).get('account_name'))
    return dict(status=status, tasks=tasks, user=user)


@admin.route('/task-admin/')
@inject(mongo=MongoDB, user_config=UserSessionConfig)
@templated('task_admin')
def task_admin(mongo, user_config):
    status, tasks = MongoTaskLoader(mongo.db, user_config).get_all_tasks()
    user = dict(account=session.get('user_params', {}).get('account_name'))
    return dict(status=status, tasks=tasks, user=user)


@inject(config=Config)
@admin.route('/create-account', methods=['POST'])
def create_account(config):
    account_config = request.json
    service = AccountCreationService(account_config['account'], account_config['username'], config)
    try:
        service.execute()
        if current_user.email == account_config['username'] and account_config['account'] not in session['accounts']:
            session['accounts'].append(account_config['account'])
        return 'OK', 200
    except Exception as ex:
        return repr(ex), 409


@inject(mongo=MongoDB)
@admin.route('/delete-account/<account_name>')
def delete_account(account_name, mongo):
    # TODO: enable account deletion
    # Account deletion disabled to prevent accidental data loss
    return 'Account deletion temporarily disabled', 401
    """
    service = AccountCreationService(account_name, '')
    try:
        # TODO: prevent deleting currently active account
        if account_name == session['user_params']['account_name']:
            raise Exception('Cannot Delete Currently Active Account!')
        service.delete_account(mongo)
        if account_name in session['accounts']:
            session['accounts'].remove(account_name)
        return 'OK', 200
    except Exception as ex:
        return repr(ex), 409
    """


@inject(auth_service=AuthServ)
@admin.route('/get-all-accounts')
def get_all_existing_accounts(auth_service):

    accounts = auth_service.get_all_accounts()
    columns = [{
        'field': 'account_name',
        'title': 'Account Name'
    }]
    return Response(dumps({'columns': columns, 'data': accounts}),
                    mimetype='application/json')


import csv
import json
import traceback
from io import StringIO

from flask import request, redirect
from flask_login import login_required
from injector import inject

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import MongoDB
from . import taskadmin
from .services.mongo_task_loader import MongoTaskLoader


@taskadmin.before_request
@login_required
def before_request():
    pass

@taskadmin.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)



@taskadmin.route('/task-admin/')
@inject(mongo=MongoDB)
@templated('task_admin')
def task_admin(mongo):

    status, tasks = MongoTaskLoader(mongo.db).get_all_tasks()
    return {'status': status, 'tasks': tasks}

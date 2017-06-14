import csv
import json
import traceback
from io import StringIO

from flask import Response
from flask import make_response
from flask import request, redirect
from flask_login import login_required
from injector import inject

from server.app.common.models import *
from server.app.common.views.decorators import templated
from server.app.injector_keys import MongoDB
from . import taskadmin
from .services.mongo_task_loader import MongoTaskLoader


@taskadmin.route('/task-admin/')
@inject(mongo=MongoDB)
@templated('task_admin')
def task_admin(mongo):

    status, tasks = MongoTaskLoader(mongo.db).get_all_tasks()
    return {'status': status, 'tasks': tasks}

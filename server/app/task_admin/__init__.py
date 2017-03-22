from flask import Blueprint

taskadmin = Blueprint('task_admin', __name__, template_folder='templates', url_prefix='/admin')

from . import views

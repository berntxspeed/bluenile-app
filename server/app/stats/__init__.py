from flask import Blueprint
from flask_login import login_required

stats = Blueprint('stats', __name__, template_folder='templates')

from . import views

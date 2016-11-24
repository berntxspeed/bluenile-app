from flask import Blueprint

stats = Blueprint('stats', __name__, template_folder='templates')

from . import views

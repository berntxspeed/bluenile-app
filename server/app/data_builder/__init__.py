from flask import Blueprint

databuilder = Blueprint('data_builder', __name__, template_folder='templates', url_prefix='/builder')

from . import views

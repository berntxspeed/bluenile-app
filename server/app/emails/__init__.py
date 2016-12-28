from flask import Blueprint

emails = Blueprint('emails', __name__, template_folder='templates')

from . import views
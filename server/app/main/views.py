from sqlalchemy.orm.exc import NoResultFound
from flask import Request, jsonify
from flask import render_template
from injector import inject

from . import main
from ..common.views import context_processors
from ..injector_keys import SQLAlchemy

@main.route('/')
@main.route('/index')
def index():
    user = {'nickname': 'Bernt'} # fake user
    return render_template('index.html',
                            title='Home',
                            user=user)


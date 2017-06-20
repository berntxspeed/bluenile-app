from flask import Request
from flask import session
from flask import abort
from flask import request, redirect
from flask_login import login_required
from injector import inject
#from premailer import transform

from . import emails
from .injector_keys import EmailServ
from ..common.views.decorators import templated
from ..common.models import Template


# Pass this function to require login for every request
@emails.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@emails.route('/mosaico-index')
@templated('mosaico_index')
def mosaico_index():
    return dict(templates=Template.query.all())

@emails.route('/editor')
@templated('editor')
def editor():
    return {}

@emails.route('/img', methods=['GET'])
@inject(request=Request, email_service=EmailServ)
def image(request, email_service):
    return email_service.image(request)

@emails.route('/upload', methods=['GET', 'POST'])
@inject(request=Request, email_service=EmailServ)
def upload(request, email_service):
    return email_service.upload(request)

@emails.route('/dl', methods=['POST'])
@inject(request=Request, email_service=EmailServ)
def download(request, email_service):
    return email_service.download(request)

@emails.route('/template', methods=['GET','POST'])
@inject(request=Request, email_service=EmailServ)
def template(request, email_service):
    return email_service.template(request)

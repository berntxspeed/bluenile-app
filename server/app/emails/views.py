from flask import request
from flask import session
from flask import Response
from flask import url_for
from flask_login import login_required
from injector import inject
from premailer import transform

from server.app.injector_keys import SQLAlchemy
from . import emails
from .injector_keys import EmailServ
from ..common.views.decorators import templated


# Pass this function to require login for every request
@emails.before_request
@login_required
def before_request():
    pass


@emails.route('/index')
@templated('index')
def index():
    return {}

@emails.route('/editor')
@templated('editor')
def editor():
    return {}

@emails.route('/img/<file>')
def image(file):
    return {}

@emails.route('/upload/<file>')
def upload(file):
    return {}

@emails.route('/dl', methods=['POST'])
def download(request):
    html = transform(request.POST['html'])
    action = request.POST['action']
    if action == 'download':
        filename = request.POST['filename']
        content_type = "text/html"
        content_disposition = "attachment; filename=%s" % filename
        response = Response(html, content_type=content_type)
        response['Content-Disposition'] = content_disposition
    elif action == 'email':
        print('attempting to send email...')
        """to = request.POST['rcpt']
        subject = request.POST['subject']
        from_email = settings.DEFAULT_FROM_EMAIL
        # TODO: convert the HTML email to a plain-text message here.  That way
        # we can have both HTML and plain text.
        msg = ""
        send_mail(subject, msg, from_email, [to], html_message=html, fail_silently=False)
        # TODO: return the mail ID here"""
        response = Response("OK: 250 OK id=12345")
    return response

@emails.route('/template/<file>')
def template(file):
    return {}
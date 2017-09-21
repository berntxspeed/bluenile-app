from injector import inject

from ...injector_keys import Config
from ...main import main


def csrf_token():
    from flask import session
    import uuid
    if not session.get('_csrf_token'):
        session['_csrf_token'] = uuid.uuid4().hex
    return session['_csrf_token']

@main.app_context_processor
@inject(config=Config)
def security_processor(config):
    return {
        'csrf_token': csrf_token,
    }

@main.app_context_processor
@inject(config=Config)
def json_config_processor(config):
    from flask import request
    from flask import session
    from flask import url_for
    from flask_login import current_user
    from json import dumps
    import uuid

    def csrf_token():
        if not session.get('_csrf_token'):
            session['_csrf_token'] = uuid.uuid4().hex
        return session['_csrf_token']

    is_authenticated = current_user.is_authenticated

    values = {
        'LOGIN_URL': url_for('auth.login', next=request.url, msg=True),
        'IS_DEBUG': config['DEBUG'],
        'CSRF_TOKEN': csrf_token(),
        'IS_AUTHENTICATED': is_authenticated,
        'FACEBOOK_APP_ID': config['FACEBOOK_APP_ID'],
        'GOOGLE_APP_ID': config['GOOGLE_APP_ID']
    }


    def json_config(varargs, kwargs):
        return dict(values.items() | kwargs.items())

    return {
        'json_config': json_config
    }

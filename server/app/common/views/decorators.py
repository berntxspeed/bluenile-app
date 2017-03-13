from flask import request
from flask import render_template
from flask import Response
from flask_login import current_user
from functools import wraps
from json import dumps
from . import context_processors


def templated(template=None, type='html'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace('.', '/') + '.' + type
            else:
                template_name += '.' + type
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator

def jsonify(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return Response(dumps(f(*args, **kwargs)), mimetype='application/json')
    return decorated_function

def login_required_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated():
            result = {
                'success': False,
                'unauthenticated': True
            }
            return Response(dumps(result), mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

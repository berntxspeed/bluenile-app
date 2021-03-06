from flask import url_for
from flask import flash
from flask import redirect
from flask_login import login_user
from flask_login import logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash

from .forms import LoginForm
from .forms import SignupForm
from .forms import FacebookSignupForm
from .forms import GoogleSignupForm
from ..common.models import User
from ..common.services import DbService

class AuthService(DbService):

    def __init__(self,
                config,
                db,
                logger,
                facebook_auth,
                google_auth,
                session):
        super(AuthService, self).__init__(config=config, db=db, logger=logger)
        self.facebook_auth = facebook_auth
        self.google_auth = google_auth

        @facebook_auth.tokengetter
        def get_facebook_token():
            return session.get('facebook_token')

        @google_auth.tokengetter
        def get_google_token():
            return session.get('google_token')

    def facebook_login(self, request):
        return self.facebook_auth.authorize(callback=url_for('auth.facebook_authorized',
                                                                next=request.args.get('next')
                                                                or request.referrer or None,
                                                                _external=True))

    def facebook_authorized(self, request, session):
        facebook_auth = self.facebook_auth
        @facebook_auth.authorized_handler
        def __facebook_authorized(resp):
            if resp is None:
                flash('There was an error logging in.')
                return redirect(url_for('auth.login'))
            next_url = self.__next_url(request)

            session['facebook_token'] = (resp['access_token'], '')

            me = facebook_auth.get('/me')
            facebook_id = me.data.get('id')
            session['facebook_id'] = facebook_id
            session['facebook_email'] = me.data.get('email')
            user = User.query.filter_by(facebook_id=facebook_id).first()
            if user is None:
                return redirect(url_for('auth.facebook_signup'))
            else:
                login_user(user, False)
                return redirect(next_url)
        return __facebook_authorized()

    def facebook_signup(self, request, session):
        facebook_id = session.get('facebook_id')
        if facebook_id is None:
            return redirect(url_for('auth.login'))
        user = User.query.filter_by(facebook_id=facebook_id).first()
        if user is not None:
            return redirect(url_for('auth.login'))
        form = FacebookSignupForm(request.form)
        if self.validate_on_submit(request, form):
            return self.__create_user(username=form.username.data,
                                      email=form.email.data,
                                      facebook_id=facebook_id)
        return {
            'form': form
        }

    def google_login(self, request):
        return self.google_auth.authorize(callback=url_for('auth.google_authorized',
                                                                next=request.args.get('next')
                                                                or request.referrer or None,
                                                                _external=True))

    def google_authorized(self, request, session):
        google_auth = self.google_auth
        @google_auth.authorized_handler
        def __google_authorized(resp):
            if resp is None:
                flash('There was an error logging in.')
                return redirect(url_for('auth.login'))
            next_url = self.__next_url(request)

            session['google_token'] = (resp['access_token'], '')

            me = google_auth.get('https://www.googleapis.com/oauth2/v1/userinfo')
            google_id = me.data.get('id')
            session['google_id'] = google_id
            session['google_email'] = me.data.get('email')
            user = User.query.filter_by(google_id=google_id).first()
            if user is None:
                return redirect(url_for('auth.google_signup'))
            else:
                login_user(user, False)
                return redirect(next_url)
        return __google_authorized()

    def google_signup(self, request, session):
        google_id = session.get('google_id')
        if google_id is None:
            return redirect(url_for('auth.login'))
        user = User.query.filter_by(google_id=google_id).first()
        if user is not None:
            return redirect(url_for('auth.login'))
        form = GoogleSignupForm(request.form)
        if self.validate_on_submit(request, form):
            return self.__create_user(username=form.username.data,
                                      email=form.email.data,
                                      google_id=google_id)
        return {
            'form': form
        }

    def login(self, request):
        form = LoginForm(request.form)
        if request.method == 'GET' and request.args.get('msg'):
            flash('Please log in first')
        if self.validate_on_submit(request, form):
            user = User.query.filter(func.lower(User.username) == func.lower(form.username.data))\
                .first()
            if user is not None and user.password_hash is not None\
                and check_password_hash(user.password_hash, form.password.data):
                login_user(user, form.remember_me.data)
                return redirect(self.__next_url(request))
            else:
                flash('Incorrect username or password.', 'error')
        return {
            'form': form
        }

    def logout(self, session):
        logout_user()
        if session.get('google_token'):
            del session['google_token']
        if session.get('google_username'):
            del session['google_username']
        if session.get('google_id'):
            del session['google_id']
        if session.get('facebook_token'):
            del session['facebook_token']
        if session.get('facebook_id'):
            del session['facebook_id']
        if session.get('facebook_email'):
            del session['facebook_email']
        flash('You have been logged out.', 'success')
        return redirect(url_for('main.index'))

    def signup(self, request):
        form = SignupForm(request.form)
        if self.validate_on_submit(request, form):
            return self.__create_user(username=form.username.data,
                                      email=form.email.data,
                                      password=form.password.data)
        return {
            'form': form
        }

    def __create_user(self,
                      username,
                      email,
                      password=None,
                      google_id=None,
                      facebook_id=None,
                      google_name=None):
        # Insert user row.
        user = User(
            username=username,
            nickname=username,
            email=email
        )
        remember_me = True
        if password:
            user.password = password
        if google_id:
            user.google_id = google_id
            remember_me = False
        if google_name:
            user.google_name = google_name
        if facebook_id:
            user.facebook_id = facebook_id
            remember_me = False
        self.db.session.add(user)
        self.db.session.commit()

        # Login user
        login_user(user, remember_me)
        return redirect(url_for('stats.special_logged_in_page'))

    def __next_url(self, request):
        next_url = request.args.get('next')
        if next_url:
            next_url = url_for('stats.special_logged_in_page')
        else:
            next_url = url_for('stats.special_logged_in_page')
        return next_url

from flask import url_for
from flask import flash
from flask import redirect
from flask_login import login_user, logout_user, UserMixin
from okta import AuthClient, UsersClient
from sqlalchemy import func

from werkzeug.security import check_password_hash
from .forms import LoginForm
from .forms import SignupForm
from ..common.models import User
from ..common.services import DbService


class OktaUser(UserMixin):
    def __init__(self, okta_user):
        self.id = okta_user.id
        self.status = okta_user.status
        self.login = okta_user.profile.login
        self.email = okta_user.profile.email
        self.firstname = okta_user.profile.firstName
        self.lastname = okta_user.profile.lastName
        self.login = okta_user.profile.login
        self.account = okta_user.profile.secondEmail

    def get_id(self):
        return self.id

    def get_account(self):
        if self.account is not None:
            return self.account.split('@')[0]


class AuthService(DbService):

    def __init__(self,
                config,
                db,
                logger,
                session):
        super(AuthService, self).__init__(config=config, db=db, logger=logger)


    def login(self, request):
        print('AuthServ Login')

        form = LoginForm(request.form)
        if request.method == 'GET' and request.args.get('msg'):
            flash('Please log in first')

        if self.validate_on_submit(request, form):
            auth_client = AuthClient('https://dev-198609.oktapreview.com', '00lKRIDx7J6jlox9LwftcKfqKqkoRSKwY5dhslMs9z')
            users_client = UsersClient('https://dev-198609.oktapreview.com', '00lKRIDx7J6jlox9LwftcKfqKqkoRSKwY5dhslMs9z')
            try:
                auth_result = auth_client.authenticate(form.username.data, form.password.data)
                okta_user = users_client.get_user(form.username.data)
            except Exception:
                auth_result = None

            if auth_result and auth_result.status == 'SUCCESS':
                user = AppUser(okta_user)
                login_user(user, form.remember_me.data)
                return redirect(self.__next_url(request))

            else:
                flash('Incorrect username or password.', 'error')
        return {
            'form': form
        }

    def logout(self, session):
        logout_user()
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
        return redirect(url_for('main.index'))

    def __next_url(self, request):
        next_url = request.args.get('next')
        if next_url:
            next_url = url_for('main.index')
        else:
            next_url = url_for('main.index')
        return next_url

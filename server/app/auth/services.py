from flask import url_for
from flask import flash
from flask import redirect
from flask_login import login_user
from flask_login import logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash

from .forms import LoginForm
from .forms import SignupForm
from ..common.models import User
from ..common.services import DbService

class AuthService(DbService):

    def __init__(self,
                config,
                db,
                logger,
                session):
        super(AuthService, self).__init__(config=config, db=db, logger=logger)


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

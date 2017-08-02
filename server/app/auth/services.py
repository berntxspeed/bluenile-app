from flask import flash
from flask import redirect, session
from flask import url_for
from flask_login import login_user, logout_user, UserMixin
from okta import AuthClient, UsersClient
from okta.framework.ApiClient import ApiClient

from .forms import LoginForm
from .forms import SignupForm

from ..common.models.system_models import session_scope
from ..common.models.system_models import ClientAccount, User, UserPermissions


class OktaUsersClient(UsersClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_user(self, uid):
        response = ApiClient.get_path(self, '/{0}'.format(uid))
        return response.json()


class OktaUser(UserMixin):
    def __init__(self, okta_user):
        self.id = okta_user.get('id')
        self.status = okta_user.get('status')
        self.login = okta_user.get('profile', {}).get('login')
        self.email = okta_user.get('profile', {}).get('email')
        self.firstname = okta_user.get('profile', {}).get('firstName')
        self.lastname = okta_user.get('profile', {}).get('lastName')
        self.account = okta_user.get('profile', {}).get('account_name')

    def get_id(self):
        return self.id


class AuthService(object):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def validate_on_submit(self, request, form):
        return request.method == 'POST' and form.validate()

    @staticmethod
    def get_user_accounts(user_email):
        # Fetch the user's authorizations
        with session_scope() as db_session:
            accounts = db_session.query(ClientAccount).join(ClientAccount.permissions) \
                .filter(UserPermissions.username == user_email)
        return accounts

    @staticmethod
    def get_all_accounts():
        with session_scope() as db_session:
            accounts = db_session.query(ClientAccount).all()
            return_dict = [dict(account_name=account.account_name) for account in accounts]
        return return_dict

    @staticmethod
    def set_user_account(account):
        # Save user/account info in the current session
        session['user_params'] = dict(account_name=account.account_name,
                                      postgres_uri=account.database_uri)

    def login(self, request):

        form = LoginForm(request.form)
        if request.method == 'GET' and request.args.get('msg'):
            flash('Please log in first')

        if self.validate_on_submit(request, form):
            okta_url, okta_api_key = self.config.get('OKTA_URL'), self.config.get('OKTA_API_KEY')
            auth_client = AuthClient(okta_url, okta_api_key)
            users_client = OktaUsersClient(okta_url, okta_api_key)
            try:
                auth_result = auth_client.authenticate(form.username.data, form.password.data)
                okta_user = users_client.get_user(form.username.data)
            except Exception:
                auth_result = None

            if auth_result and auth_result.status == 'SUCCESS':
                user = OktaUser(okta_user)
                login_user(user, form.remember_me.data)

                accounts = self.get_user_accounts(user.email)
                session['accounts'] = [account.account_name for account in accounts]

                # Save user/account info in the current session
                first_account = accounts.first()
                if first_account is not None:
                    self.set_user_account(accounts.first())
                    return redirect(self.__next_url(request))
                else:
                    flash('User is not associated with any current account', 'error')
                    logout_user()
            else:
                flash('Incorrect username or password.', 'error')
        return {
            'form': form
        }

    @staticmethod
    def logout():
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

# TODO: self.db.session needs to be re-referenced to support this method
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
        # self.db.session.add(user)
        # self.db.session.commit()

        # Login user
        login_user(user, remember_me)
        return redirect(url_for('main.index'))

    def __next_url(self, request):
        next_url = request.args.get('next')
        return next_url or url_for('main.index')

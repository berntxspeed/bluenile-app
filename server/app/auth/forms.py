from sqlalchemy import func
from werkzeug.security import check_password_hash
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import TextAreaField
from wtforms import TextField
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Optional
from wtforms.validators import Regexp
from wtforms.validators import Required
from wtforms.validators import URL
from wtforms.validators import ValidationError

from ..common.forms import BaseForm
from ..common.forms.validators import MaxLength
from ..common.forms.validators import MinLength
from ..common.models.system_models import User

# Messages

EMAIL_REQUIRED_MSG = 'Your email address is required.'
EMAIL_INVALID_MSG = 'Enter a valid email address.'
EMAIL_EXISTS_MSG = 'That email address is already in use.'
CHANGE_EMAIL_EXISTS_MSG = '{0} is already in use.'

PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 30
PASSWORD_REQUIRED_MSG = 'Enter a password.'
PASSWORD_CONFIRM_MSG = 'Your passwords do not match.'
PASSWORD_LOGIN_REQUIRED_MSG = 'Enter your password.'

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 16
USERNAME_REQUIRED_MSG = 'Enter a username.'
USERNAME_REGEX_MSG = ('Your username must be alphanumeric and can contain underscores and be '
                      'separated by spaces.')
USERNAME_EXISTS_MSG = 'That username is taken.'
USERNAME_REGEX = r"^[\w\.]+(?:\s[\w\.]+)*$"
USERNAME_LOGIN_REQUIRED_MSG = 'Enter your username.'

# Validators

EMAIL_VALIDATORS = (
    Required(message=EMAIL_REQUIRED_MSG),
    Email(message=EMAIL_INVALID_MSG)
)

PASSWORD_VALIDATORS = (
    Required(message=PASSWORD_REQUIRED_MSG),
    MinLength(PASSWORD_MIN_LENGTH),
    MaxLength(PASSWORD_MAX_LENGTH),
    EqualTo('confirm_password', message=PASSWORD_CONFIRM_MSG),
)

USERNAME_VALIDATORS = (
    Required(message=USERNAME_REQUIRED_MSG),
    MinLength(USERNAME_MIN_LENGTH),
    MaxLength(USERNAME_MAX_LENGTH),
    Regexp(USERNAME_REGEX, message=USERNAME_REGEX_MSG)
)


# Forms

def validate_email(field):
    if User.query.filter(func.lower(User.email) == func.lower(field.data)).first():
        raise ValidationError(EMAIL_EXISTS_MSG)


def validate_username(field):
    if User.query.filter(func.lower(User.username) == func.lower(field.data)).first():
        raise ValidationError(USERNAME_EXISTS_MSG)


class ChangePasswordForm(BaseForm):
    old_password = PasswordField('Old Password', validators=[Required('Enter your old password.')])
    password = PasswordField('New Password', validators=PASSWORD_VALIDATORS)
    confirm_password = PasswordField('Confirm')

    def __init__(self, user=None, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_old_password(self, field):
        if not check_password_hash(self.user.password_hash, field.data):
            raise ValidationError('Incorrect password')


class ChangeEmailForm(BaseForm):
    email = TextField('New Email', validators=EMAIL_VALIDATORS)

    def validate_email(self, field):
        validate_email(field)


class LoginForm(BaseForm):
    username = TextField('Username', validators=[Required(USERNAME_LOGIN_REQUIRED_MSG)])
    password = PasswordField('Password', validators=[Required(PASSWORD_LOGIN_REQUIRED_MSG)])
    remember_me = BooleanField('')


class SignupForm(BaseForm):
    username = TextField('Username', validators=USERNAME_VALIDATORS)
    email = TextField('Email', validators=EMAIL_VALIDATORS)
    password = PasswordField('Password', validators=PASSWORD_VALIDATORS)
    confirm_password = PasswordField('Confirm')

    def validate_email(self, field):
        validate_email(field)

    def validate_username(self, field):
        validate_username(field)


class GoogleSignupForm(BaseForm):
    username = TextField('Username', validators=USERNAME_VALIDATORS)
    email = TextField('Email', validators=EMAIL_VALIDATORS)

    def validate_email(self, field):
        validate_email(field)

    def validate_username(self, field):
        validate_username(field)


class FacebookSignupForm(BaseForm):
    username = TextField('Username', validators=USERNAME_VALIDATORS)
    email = TextField('Email', validators=EMAIL_VALIDATORS)

    def validate_email(self, field):
        validate_email(field)

    def validate_username(self, field):
        validate_username(field)


class ForgotPasswordForm(BaseForm):
    email = TextField('Email', validators=EMAIL_VALIDATORS)


class ResetPasswordForm(BaseForm):
    email = TextField('Email', validators=EMAIL_VALIDATORS)
    password = PasswordField('Password', validators=PASSWORD_VALIDATORS)
    confirm_password = PasswordField('Confirm')

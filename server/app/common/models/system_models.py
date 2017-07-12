from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import synonym, relationship, backref, sessionmaker
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

HASH_SECRET = b'33jjfSFTW43FE2992222FD'

system_db = SQLAlchemy(session_options={
    'autocommit': False,
    'autoflush': False
})


class User(UserMixin, system_db.Model):
    __tablename__ = 'users'
    id = system_db.Column(system_db.Integer, primary_key=True)
    password_hash = system_db.Column(system_db.String(128))
    facebook_id = system_db.Column(system_db.String(255), unique=True)
    twitter_id = system_db.Column(system_db.String(255), unique=True)
    twitter_name = system_db.Column(system_db.String(128))
    google_id = system_db.Column(system_db.String(255), unique=True)
    username = system_db.Column(system_db.String(255), nullable=False, unique=True)
    nickname = system_db.Column(system_db.String(64), nullable=True)
    email = system_db.Column(system_db.String(64), nullable=True)

    # created_at = system_db.Column(system_db.DateTime())

    def __init__(self, username=None, password=None, id=None, email=None, nickname=None):
        if username:
            self.username = username
            if not nickname:
                self.nickname = username
        if nickname:
            self.nickname = nickname
        if password:
            self.password = password
        if id:
            self.id = id
        if email:
            self.email = email

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def insert_users():
        users = [
            User(username='bernt', password='Temp@12345', id=1)
        ]
        for user in users:
            usr = User.query.filter_by(id=user.id).first()
            if usr is None:
                system_db.session.add(user)
        system_db.session.commit()

    def __repr__(self):
        return '<User %r>' % self.username


@system_db.event.listens_for(User, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    u = User.query.filter_by(id=target.id).first()
    if u is None:
        return target
    u = User.query.order_by(User.id.desc()).first()
    target.id = u.id + 1
    return target


class UserPermissions(system_db.Model):
    __tablename__ = 'user_permissions'
    id = system_db.Column(system_db.String(255), primary_key=True)
    account_id = system_db.Column(system_db.String(255))


class ClientAccount(system_db.Model):
    __tablename__ = 'client_account'
    id = system_db.Column(system_db.String(255), primary_key=True)
    # account_id = system_db.Column(system_db.String(255), unique=True)
    database_uri = system_db.Column(system_db.String(255), unique=True)  # can be just the client id

    users = relationship(UserPermissions, backref='client_account',
                         primaryjoin='ClientAccount.id==UserPermissions.account_id',
                         foreign_keys=[UserPermissions.account_id],
                         passive_deletes='all')

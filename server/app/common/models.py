from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(128))
    facebook_id = db.Column(db.String(255), unique=True)
    twitter_id = db.Column(db.String(255), unique=True)
    twitter_name = db.Column(db.String(128))
    username = db.Column(db.String(255), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(64), nullable=True)
    #created_at = db.Column(db.DateTime())

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

class KeyValue(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)

    def __init__(self, key, value, created_at=None):
        self.key = key
        self.value = value
        if created_at is None:
            self.created_at = datetime.datetime.utcnow()

    @staticmethod
    def insert_keyvalues():
        kvs = {
            'hello': 'world',
            'goodbye': 'cruel world'
        }
        for key, value in kvs.items():
            kv = KeyValue.query.filter_by(key=key).first()
            if kv is None:
                kv = KeyValue(key=key, value=value)
                db.session.add(kv)
        db.session.commit()

    def serializable(self):
        return

    def __repr__(self):
        return '<KeyValue %r>' % self.key

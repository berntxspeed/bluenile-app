import datetime

import hmac
import base64
import hashlib
HASH_SECRET = b'33jjfSFTW43FE2992222FD'

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSON, TEXT
from sqlalchemy.types import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym, relationship, backref, sessionmaker
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from .utils.event_mgr import EventMgr

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(128))
    facebook_id = db.Column(db.String(255), unique=True)
    twitter_id = db.Column(db.String(255), unique=True)
    twitter_name = db.Column(db.String(128))
    google_id = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(64), nullable=True)
    #created_at = db.Column(db.DateTime())

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
            User(username='bernt', password='pass', id=1),
            User(username='val', password='pass', id=2)
        ]
        for user in users:
            usr = User.query.filter_by(id=user.id).first()
            if usr is None:
                db.session.add(user)
        db.session.commit()

    def __repr__(self):
        return '<User %r>' % self.username

@db.event.listens_for(User, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    u = User.query.filter_by(id=target.id).first()
    if u is None:
        return target
    u = User.query.order_by(User.id.desc()).first()
    target.id = u.id + 1
    return target

class KeyValue(db.Model):
    __tablename__ = 'key_value'
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255))
    price = db.Column(db.Float)
    done = db.Column(db.Boolean)
    count = db.Column(db.Integer)
    created_at = db.Column(TIMESTAMP)
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    def __init__(self, key, value, created_at=None):
        self.key = key
        self.value = value
        if created_at is None:
            self.created_at = datetime.datetime.utcnow()

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

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

@db.event.listens_for(KeyValue, 'before_update', retval=True)
def on_update(mapper, connection, target):
    print('record ' + target.__repr__() + ' was updated at: ' + str(datetime.datetime.utcnow()))
    target._last_updated = datetime.datetime.utcnow()
    return target


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.BigInteger, primary_key=True)
    def_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(TIMESTAMP)
    rec_id = db.Column(db.Integer, nullable=False)
    old_val = db.Column(db.String(255))
    new_val = db.Column(db.String(255))

    # metadata for later us as this feature evolves past just old/new val
    meta = db.Column(JSON)

@db.event.listens_for(Event, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.timestamp = datetime.datetime.utcnow()
    return target


class EventDefinition(db.Model):
    __tablename__ = 'event_def'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    desc = db.Column(db.String(1024))
    created_at = db.Column(TIMESTAMP)
    table = db.Column(db.String(255))
    dml_op = db.Column(db.String(255)) # should only be 'insert' or 'update'
    column = db.Column(db.String(255)) # refers to the column to watch
    old_val = db.Column(db.String(255)) # blank signifies not caring what the old val is - track all events where val is changed to new_val value
    new_val = db.Column(db.String(255)) # blank signifies not caring what the new val is - just track all changes

    # event_config for later use as this feature evolves past just old/new val = x/y
    event_config = db.Column(JSON) # might need JSON(astext_type=Text())

    events = relationship(Event, backref='event_def',
                             primaryjoin='EventDefinition.id==Event.def_id',
                             foreign_keys=[Event.def_id],
                             passive_deletes='all')

@db.event.listens_for(EventDefinition, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    return target


class Purchase(db.Model):
    __tablename__ = 'purchase'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.String(255), unique=True)
    customer_id = db.Column(db.String(255))
    created_at = db.Column(TIMESTAMP)
    price = db.Column(db.Float)
    is_paid = db.Column(db.Boolean)
    referring_site = db.Column(db.String(255))
    landing_site = db.Column(db.String(255))
    browser_ip = db.Column(db.String(255))
    user_agent = db.Column(db.String(255))
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    events = relationship(Event, backref='purchase',
                          primaryjoin='Purchase.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

@db.event.listens_for(Purchase, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    return target

@db.event.listens_for(Purchase, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class EmlSend(db.Model):
    __tablename__ = 'eml_send'
    id = db.Column(db.Integer, primary_key=True)
    SendID = db.Column(db.Integer)
    SubscriberKey = db.Column(db.String(255))
    EmailAddress = db.Column(db.String(255))
    EventDate = db.Column(TIMESTAMP)
    TriggeredSendExternalKey = db.Column(db.String(255))
    _day = db.Column(db.Integer) # auto-calculated 0-mon 6-sun
    _hour = db.Column(db.Integer)
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_send',
                          primaryjoin='EmlSend.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlSend %r>' % self.SubscriberKey

@db.event.listens_for(EmlSend, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target

@db.event.listens_for(EmlSend, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target

class EmlOpen(db.Model):
    __tablename__ = 'eml_open'
    id = db.Column(db.Integer, primary_key=True)
    SendID = db.Column(db.Integer)
    SubscriberKey = db.Column(db.String(255))
    EmailAddress = db.Column(db.String(255))
    EventDate = db.Column(TIMESTAMP)
    TriggeredSendExternalKey = db.Column(db.String(255))
    IsUnique = db.Column(db.Boolean)
    IpAddress = db.Column(db.String(255))
    Country = db.Column(db.String(255))
    Region = db.Column(db.String(255))
    City = db.Column(db.String(255))
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    MetroCode = db.Column(db.String(255))
    AreaCode = db.Column(db.String(255))
    Browser = db.Column(db.String(255))
    EmailClient = db.Column(db.String(255))
    OperatingSystem = db.Column(db.String(255))
    Device = db.Column(db.String(255))
    _day = db.Column(db.Integer) # auto-calculated 0-mon 6-sun
    _hour = db.Column(db.Integer)
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_open',
                          primaryjoin='EmlOpen.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlOpen %r>' % self.SubscriberKey

@db.event.listens_for(EmlOpen, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target

@db.event.listens_for(EmlOpen, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target

class EmlClick(db.Model):
    __tablename__ = 'eml_click'
    id = db.Column(db.Integer, primary_key=True)
    SendID = db.Column(db.Integer)
    SubscriberKey = db.Column(db.String(255))
    EmailAddress = db.Column(db.String(255))
    EventDate = db.Column(TIMESTAMP)
    SendURLID = db.Column(db.String(255))
    URLID = db.Column(db.String(255))
    URL = db.Column(db.String(1024))
    Alias = db.Column(db.String(255))
    TriggeredSendExternalKey = db.Column(db.String(255))
    IsUnique = db.Column(db.Boolean)
    IpAddress = db.Column(db.String(255))
    Country = db.Column(db.String(255))
    Region = db.Column(db.String(255))
    City = db.Column(db.String(255))
    Latitude = db.Column(db.Float)
    Longitude = db.Column(db.Float)
    MetroCode = db.Column(db.String(255))
    AreaCode = db.Column(db.String(255))
    Browser = db.Column(db.String(255))
    EmailClient = db.Column(db.String(255))
    OperatingSystem = db.Column(db.String(255))
    Device = db.Column(db.String(255))
    _day = db.Column(db.Integer) # auto-calculated 0-mon 6-sun
    _hour = db.Column(db.Integer)
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_click',
                          primaryjoin='EmlClick.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlClick %r>' % self.SubscriberKey

@db.event.listens_for(EmlClick, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target

@db.event.listens_for(EmlClick, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target

class SendJob(db.Model):
    __tablename__ = 'send_job'
    id = db.Column(db.Integer, primary_key=True)
    SendID = db.Column(db.Integer, unique=True) # SendID Field
    TriggeredSendExternalKey = db.Column(db.String(255))
    SendDefinitionExternalKey = db.Column(db.String(255))
    SchedTime = db.Column(TIMESTAMP)
    SentTime = db.Column(TIMESTAMP)
    EmailName= db.Column(db.String(64))
    Subject = db.Column(db.String(1024))
    PreviewURL = db.Column(db.String(1024))
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)
    eml_sends = relationship(EmlSend, backref='send_job',
                             primaryjoin='SendJob.SendID==EmlSend.SendID',
                             foreign_keys=[EmlSend.SendID],
                             passive_deletes='all')
    eml_opens = relationship(EmlOpen, backref='send_job',
                             primaryjoin='SendJob.SendID==EmlOpen.SendID',
                             foreign_keys=[EmlOpen.SendID],
                             passive_deletes='all')
    eml_clicks = relationship(EmlClick, backref='send_job',
                              primaryjoin='SendJob.SendID==EmlClick.SendID',
                              foreign_keys=[EmlClick.SendID],
                              passive_deletes='all')
    num_sends = db.Column(db.Integer)
    num_opens = db.Column(db.Integer)
    num_clicks = db.Column(db.Integer)

    def _get_stats(self):
        self.num_sends = db.session.object_session(self).query(EmlSend).with_parent(self, "eml_sends").count()
        self.num_opens = db.session.object_session(self).query(EmlOpen).with_parent(self, "eml_opens").count()
        self.num_clicks = db.session.object_session(self).query(EmlClick).with_parent(self, "eml_clicks").count()
        db.session.add(self)
        db.session.commit()


    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<SendJob %r>' % self.SendID

@db.event.listens_for(SendJob, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target

class Artist(db.Model):
    name = db.Column(db.String(128), primary_key=True)
    popularity = db.Column(db.String(128))
    uri = db.Column(db.String(256))
    href = db.Column(db.String(256))
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Artist %r>' % self.name

@db.event.listens_for(Artist, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target

class WebTrackingEvent(db.Model):
    __tablename__ = 'web_tracking_event'
    id = db.Column(db.Integer, primary_key=True)
    browser_id = db.Column(db.String(255)) #primary key
    utc_millisecs = db.Column(TIMESTAMP) #primary key
    hashed_email = db.Column(db.String(255))
    event_category = db.Column(db.String(255))
    event_action = db.Column(db.String(255))
    event_label = db.Column(db.String(255))
    event_value = db.Column(db.Float)
    sessions_with_event = db.Column(db.Integer)

    browser = db.Column(db.String(255))
    browser_size = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))
    device_category = db.Column(db.String(255))
    mobile_device_branding = db.Column(db.String(255))
    mobile_device_model = db.Column(db.String(255))

    country = db.Column(db.String(255))
    region = db.Column(db.String(255))
    metro = db.Column(db.String(255))
    city = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    events = relationship(Event, backref='web_tracking_event',
                          primaryjoin='WebTrackingEvent.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

class WebTrackingPageView(db.Model):
    __tablename__ = 'web_tracking_page_view'
    id = db.Column(db.Integer, primary_key=True)
    browser_id = db.Column(db.String(255)) #primary key
    utc_millisecs = db.Column(TIMESTAMP) #primary key
    hashed_email = db.Column(db.String(255))
    page_path = db.Column(db.String(500))
    page_views = db.Column(db.Integer)
    page_value = db.Column(db.Float)
    sessions = db.Column(db.Integer)

    browser = db.Column(db.String(255))
    browser_size = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))
    device_category = db.Column(db.String(255))
    mobile_device_branding = db.Column(db.String(255))
    mobile_device_model = db.Column(db.String(255))

    country = db.Column(db.String(255))
    region = db.Column(db.String(255))
    metro = db.Column(db.String(255))
    city = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    events = relationship(Event, backref='web_tracking_page_view',
                          primaryjoin='WebTrackingPageView.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

class WebTrackingEcomm(db.Model):
    __tablename__ = 'web_tracking_ecomm'
    id = db.Column(db.Integer, primary_key=True)
    browser_id = db.Column(db.String(255)) #primary key
    utc_millisecs = db.Column(TIMESTAMP) #primary key
    hashed_email = db.Column(db.String(255))
    total_value = db.Column(db.Float)
    item_quantity = db.Column(db.Integer)
    product_detail_views = db.Column(db.Integer)

    browser = db.Column(db.String(255))
    browser_size = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))
    device_category = db.Column(db.String(255))
    mobile_device_branding = db.Column(db.String(255))
    mobile_device_model = db.Column(db.String(255))

    country = db.Column(db.String(255))
    region = db.Column(db.String(255))
    metro = db.Column(db.String(255))
    city = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    events = relationship(Event, backref='web_tracking_ecomm',
                          primaryjoin='WebTrackingEcomm.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(255), unique=True)
    email_address = db.Column(db.String(255))
    hashed_email = db.Column(db.String(255))
    fname = db.Column(db.String(255))
    lname = db.Column(db.String(255))
    marketing_allowed = db.Column(db.Boolean)
    created_at = db.Column(TIMESTAMP)
    purchase_count = db.Column(db.Integer)
    total_spent_so_far = db.Column(db.Float)
    _last_updated = db.Column(TIMESTAMP)
    _last_ext_sync = db.Column(TIMESTAMP)
    purchases = relationship(Purchase, backref='customer',
                             primaryjoin='Customer.customer_id==Purchase.customer_id',
                             foreign_keys=[Purchase.customer_id],
                             passive_deletes='all')
    eml_sends = relationship(EmlSend, backref='customer',
                             primaryjoin='Customer.email_address==EmlSend.EmailAddress',
                             foreign_keys=[EmlSend.EmailAddress],
                             passive_deletes='all')
    eml_opens = relationship(EmlOpen, backref='customer',
                             primaryjoin='Customer.email_address==EmlOpen.EmailAddress',
                             foreign_keys=[EmlOpen.EmailAddress],
                             passive_deletes='all')
    eml_clicks = relationship(EmlClick, backref='customer',
                             primaryjoin='Customer.email_address==EmlClick.EmailAddress',
                             foreign_keys=[EmlClick.EmailAddress],
                             passive_deletes='all')
    web_tracking_events = relationship(WebTrackingEvent, backref='customer',
                                       primaryjoin='Customer.hashed_email==WebTrackingEvent.hashed_email',
                                       foreign_keys=[WebTrackingEvent.hashed_email],
                                       passive_deletes='all')

    web_tracking_page_views = relationship(WebTrackingPageView, backref='customer',
                                       primaryjoin='Customer.hashed_email==WebTrackingPageView.hashed_email',
                                       foreign_keys=[WebTrackingPageView.hashed_email],
                                       passive_deletes='all')

    web_tracking_ecomms = relationship(WebTrackingEcomm, backref='customer',
                                       primaryjoin='Customer.hashed_email==WebTrackingEcomm.hashed_email',
                                       foreign_keys=[WebTrackingEcomm.hashed_email],
                                       passive_deletes='all')

    events = relationship(Event, backref='customer',
                          primaryjoin='Customer.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr(self):
        return '<Customer %r>' % self.customer_id

@db.event.listens_for(Customer, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    target.hashed_email = base64.b64encode(hmac.new(HASH_SECRET,
                                                    msg=target.email_address.encode('utf-8'),
                                                    digestmod=hashlib.sha256).digest()).hex()
    return target

@db.event.listens_for(Customer, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class Upload(db.Model):
    __tablename__ = 'upload'
    name = db.Column(db.String(200), primary_key=True)
    image = db.Column(db.LargeBinary)
    last_modified = db.Column(TIMESTAMP)
    created = db.Column(TIMESTAMP)
    esp_hosted_url = db.Column(db.String(255))
    esp_hosted_key = db.Column(db.String(255))
    esp_hosted_id = db.Column(db.String(255))
    esp_hosted_category_id = db.Column(db.String(255))
    image_size_height = db.Column(db.Integer)
    image_size_width = db.Column(db.Integer)

@db.event.listens_for(Upload, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    return target

@db.event.listens_for(Upload, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target

class Template(db.Model):
    __tablename__ = 'template'
    key = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    html = db.Column(TEXT)
    last_modified = db.Column(TIMESTAMP)
    created = db.Column(TIMESTAMP)
    template_data = db.Column(JSON(astext_type=Text()))
    meta_data = db.Column(JSON(astext_type=Text()))

    def get_key(self, name=None):
        if name is None:
            name = self.name
        return abs(hash(name)) % (10 ** 7)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.key)

@db.event.listens_for(Template, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    target.key = hashlib.md5(target.name.encode()).hexdigest()[0:7]
    return target

@db.event.listens_for(Template, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    table = db.Column(db.String(255))
    grp_by_first = db.Column(db.String(255))
    grp_by_second = db.Column(db.String(255))
    aggregate_op = db.Column(db.String(255))
    aggregate_field = db.Column(db.String(255))
    graph_type = db.Column(db.String(255))
    filters_json = db.Column(JSON(astext_type=Text()))
    created = db.Column(TIMESTAMP)
    last_modified = db.Column(TIMESTAMP)

@db.event.listens_for(Report, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    return target

@db.event.listens_for(Report, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target
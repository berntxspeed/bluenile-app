import base64
import datetime
import hashlib
import hmac
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSON, TEXT
from sqlalchemy.types import Text
from sqlalchemy.orm import relationship

HASH_SECRET = b'33jjfSFTW43FE2992222FD'


user_db = SQLAlchemy(session_options={
    'autocommit': False,
    'autoflush': False
})


class KeyValue(user_db.Model):
    __tablename__ = 'key_value'
    key = user_db.Column(user_db.String(64), primary_key=True)
    value = user_db.Column(user_db.String(255))
    price = user_db.Column(user_db.Float)
    done = user_db.Column(user_db.Boolean)
    count = user_db.Column(user_db.Integer)
    created_at = user_db.Column(TIMESTAMP)
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

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
                user_db.session.add(kv)
        user_db.session.commit()

    def serializable(self):
        return

    def __repr__(self):
        return '<KeyValue %r>' % self.key


@user_db.event.listens_for(KeyValue, 'before_update', retval=True)
def on_update(mapper, connection, target):
    print('record ' + target.__repr__() + ' was updated at: ' + str(datetime.datetime.utcnow()))
    target._last_updated = datetime.datetime.utcnow()
    return target


class Event(user_db.Model):
    __tablename__ = 'event'
    id = user_db.Column(user_db.BigInteger, primary_key=True)
    def_id = user_db.Column(user_db.Integer, nullable=False)
    timestamp = user_db.Column(TIMESTAMP)
    rec_id = user_db.Column(user_db.Integer, nullable=False)
    old_val = user_db.Column(user_db.String(255))
    new_val = user_db.Column(user_db.String(255))

    # metadata for later us as this feature evolves past just old/new val
    meta = user_db.Column(JSON)


@user_db.event.listens_for(Event, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.timestamp = datetime.datetime.utcnow()
    return target


class EventDefinition(user_db.Model):
    __tablename__ = 'event_def'
    id = user_db.Column(user_db.Integer, primary_key=True)
    name = user_db.Column(user_db.String(255), unique=True)
    desc = user_db.Column(user_db.String(1024))
    created_at = user_db.Column(TIMESTAMP)
    table = user_db.Column(user_db.String(255))
    dml_op = user_db.Column(user_db.String(255))  # should only be 'insert' or 'update'
    column = user_db.Column(user_db.String(255))  # refers to the column to watch
    old_val = user_db.Column(user_db.String(
        255))  # blank signifies not caring what the old val is - track all events where val is changed to new_val value
    new_val = user_db.Column(user_db.String(255))  # blank signifies not caring what the new val is - just track all changes

    # event_config for later use as this feature evolves past just old/new val = x/y
    event_config = user_db.Column(JSON)  # might need JSON(astext_type=Text())

    events = relationship(Event, backref='event_def',
                          primaryjoin='EventDefinition.id==Event.def_id',
                          foreign_keys=[Event.def_id],
                          passive_deletes='all')


@user_db.event.listens_for(EventDefinition, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    return target


class Purchase(user_db.Model):
    __tablename__ = 'purchase'
    id = user_db.Column(user_db.Integer, primary_key=True)
    purchase_id = user_db.Column(user_db.String(255), unique=True)
    customer_id = user_db.Column(user_db.String(255))
    created_at = user_db.Column(TIMESTAMP)
    price = user_db.Column(user_db.Float)
    is_paid = user_db.Column(user_db.Boolean)
    referring_site = user_db.Column(user_db.String(255))
    landing_site = user_db.Column(user_db.String(255))
    browser_ip = user_db.Column(user_db.String(255))
    user_agent = user_db.Column(user_db.String(255))
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

    events = relationship(Event, backref='purchase',
                          primaryjoin='Purchase.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()


@user_db.event.listens_for(Purchase, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    return target


@user_db.event.listens_for(Purchase, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class StgEmlSend(user_db.Model):
    __tablename__ = 'stg_eml_send'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)


class EmlSend(user_db.Model):
    __tablename__ = 'eml_send'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_send',
                          primaryjoin='EmlSend.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlSend %r>' % self.SubscriberKey


@user_db.event.listens_for(EmlSend, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target


@user_db.event.listens_for(EmlSend, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class StgEmlOpen(user_db.Model):
    __tablename__ = 'stg_eml_open'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    IsUnique = user_db.Column(user_db.Boolean)
    IpAddress = user_db.Column(user_db.String(255))
    Country = user_db.Column(user_db.String(255))
    Region = user_db.Column(user_db.String(255))
    City = user_db.Column(user_db.String(255))
    Latitude = user_db.Column(user_db.Float)
    Longitude = user_db.Column(user_db.Float)
    MetroCode = user_db.Column(user_db.String(255))
    AreaCode = user_db.Column(user_db.String(255))
    Browser = user_db.Column(user_db.String(255))
    EmailClient = user_db.Column(user_db.String(255))
    OperatingSystem = user_db.Column(user_db.String(255))
    Device = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)


class EmlOpen(user_db.Model):
    __tablename__ = 'eml_open'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    IsUnique = user_db.Column(user_db.Boolean)
    IpAddress = user_db.Column(user_db.String(255))
    Country = user_db.Column(user_db.String(255))
    Region = user_db.Column(user_db.String(255))
    City = user_db.Column(user_db.String(255))
    Latitude = user_db.Column(user_db.Float)
    Longitude = user_db.Column(user_db.Float)
    MetroCode = user_db.Column(user_db.String(255))
    AreaCode = user_db.Column(user_db.String(255))
    Browser = user_db.Column(user_db.String(255))
    EmailClient = user_db.Column(user_db.String(255))
    OperatingSystem = user_db.Column(user_db.String(255))
    Device = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_open',
                          primaryjoin='EmlOpen.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlOpen %r>' % self.SubscriberKey


@user_db.event.listens_for(EmlOpen, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target


@user_db.event.listens_for(EmlOpen, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class StgEmlClick(user_db.Model):
    __tablename__ = 'stg_eml_click'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    SendURLID = user_db.Column(user_db.String(255))
    URLID = user_db.Column(user_db.String(255))
    URL = user_db.Column(user_db.String(1024))
    Alias = user_db.Column(user_db.String(255))
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    IsUnique = user_db.Column(user_db.Boolean)
    IpAddress = user_db.Column(user_db.String(255))
    Country = user_db.Column(user_db.String(255))
    Region = user_db.Column(user_db.String(255))
    City = user_db.Column(user_db.String(255))
    Latitude = user_db.Column(user_db.Float)
    Longitude = user_db.Column(user_db.Float)
    MetroCode = user_db.Column(user_db.String(255))
    AreaCode = user_db.Column(user_db.String(255))
    Browser = user_db.Column(user_db.String(255))
    EmailClient = user_db.Column(user_db.String(255))
    OperatingSystem = user_db.Column(user_db.String(255))
    Device = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)


class EmlClick(user_db.Model):
    __tablename__ = 'eml_click'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer)
    SubscriberKey = user_db.Column(user_db.String(255))
    EmailAddress = user_db.Column(user_db.String(255))
    EventDate = user_db.Column(TIMESTAMP)
    SendURLID = user_db.Column(user_db.String(255))
    URLID = user_db.Column(user_db.String(255))
    URL = user_db.Column(user_db.String(1024))
    Alias = user_db.Column(user_db.String(255))
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    IsUnique = user_db.Column(user_db.Boolean)
    IpAddress = user_db.Column(user_db.String(255))
    Country = user_db.Column(user_db.String(255))
    Region = user_db.Column(user_db.String(255))
    City = user_db.Column(user_db.String(255))
    Latitude = user_db.Column(user_db.Float)
    Longitude = user_db.Column(user_db.Float)
    MetroCode = user_db.Column(user_db.String(255))
    AreaCode = user_db.Column(user_db.String(255))
    Browser = user_db.Column(user_db.String(255))
    EmailClient = user_db.Column(user_db.String(255))
    OperatingSystem = user_db.Column(user_db.String(255))
    Device = user_db.Column(user_db.String(255))
    _day = user_db.Column(user_db.Integer)  # auto-calculated 0-mon 6-sun
    _hour = user_db.Column(user_db.Integer)
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

    events = relationship(Event, backref='eml_click',
                          primaryjoin='EmlClick.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<EmlClick %r>' % self.SubscriberKey


@user_db.event.listens_for(EmlClick, 'before_insert', retval=True)
def on_insert(mapper, connection, target):
    if target.EventDate is not None:
        target._day = target.EventDate.weekday()
        target._hour = target.EventDate.hour
    return target


@user_db.event.listens_for(EmlClick, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class StgSendJob(user_db.Model):
    __tablename__ = 'stg_send_job'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer, unique=True)  # SendID Field
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    SendDefinitionExternalKey = user_db.Column(user_db.String(255))
    SchedTime = user_db.Column(TIMESTAMP)
    SentTime = user_db.Column(TIMESTAMP)
    EmailName = user_db.Column(user_db.String(255))
    Subject = user_db.Column(user_db.String(1024))
    PreviewURL = user_db.Column(user_db.String(1024))


class SendJob(user_db.Model):
    __tablename__ = 'send_job'
    id = user_db.Column(user_db.Integer, primary_key=True)
    SendID = user_db.Column(user_db.Integer, unique=True)  # SendID Field
    TriggeredSendExternalKey = user_db.Column(user_db.String(255))
    SendDefinitionExternalKey = user_db.Column(user_db.String(255))
    SchedTime = user_db.Column(TIMESTAMP)
    SentTime = user_db.Column(TIMESTAMP)
    EmailName = user_db.Column(user_db.String(255))
    Subject = user_db.Column(user_db.String(1024))
    PreviewURL = user_db.Column(user_db.String(1024))
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)
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
    num_sends = user_db.Column(user_db.Integer)
    num_opens = user_db.Column(user_db.Integer)
    num_clicks = user_db.Column(user_db.Integer)

    def _get_stats(self):
        self.num_sends = user_db.session.object_session(self).query(EmlSend).with_parent(self, "eml_sends").count()
        self.num_opens = user_db.session.object_session(self).query(EmlOpen).filter(EmlOpen.IsUnique == True).with_parent(
            self, "eml_opens").count()
        self.num_clicks = user_db.session.object_session(self).query(EmlClick).filter(EmlClick.IsUnique == True).with_parent(
            self, "eml_clicks").count()
        user_db.session.add(self)
        user_db.session.commit()

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<SendJob %r>' % self.SendID


@user_db.event.listens_for(SendJob, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class Artist(user_db.Model):
    name = user_db.Column(user_db.String(128), primary_key=True)
    popularity = user_db.Column(user_db.String(128))
    uri = user_db.Column(user_db.String(256))
    href = user_db.Column(user_db.String(256))
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)

    def _update_last_ext_sync(self):
        self._last_ext_sync = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Artist %r>' % self.name


@user_db.event.listens_for(Artist, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class WebTrackingEvent(user_db.Model):
    __tablename__ = 'web_tracking_event'
    id = user_db.Column(user_db.Integer, primary_key=True)
    browser_id = user_db.Column(user_db.String(255))  # primary key
    utc_millisecs = user_db.Column(TIMESTAMP)  # primary key
    hashed_email = user_db.Column(user_db.String(255))
    event_category = user_db.Column(user_db.String(255))
    event_action = user_db.Column(user_db.String(255))
    event_label = user_db.Column(user_db.String(255))
    event_value = user_db.Column(user_db.Float)
    sessions_with_event = user_db.Column(user_db.Integer)

    browser = user_db.Column(user_db.String(255))
    browser_size = user_db.Column(user_db.String(255))
    operating_system = user_db.Column(user_db.String(255))
    device_category = user_db.Column(user_db.String(255))
    mobile_device_branding = user_db.Column(user_db.String(255))
    mobile_device_model = user_db.Column(user_db.String(255))

    country = user_db.Column(user_db.String(255))
    region = user_db.Column(user_db.String(255))
    metro = user_db.Column(user_db.String(255))
    city = user_db.Column(user_db.String(255))
    latitude = user_db.Column(user_db.Float)
    longitude = user_db.Column(user_db.Float)

    events = relationship(Event, backref='web_tracking_event',
                          primaryjoin='WebTrackingEvent.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


class WebTrackingPageView(user_db.Model):
    __tablename__ = 'web_tracking_page_view'
    id = user_db.Column(user_db.Integer, primary_key=True)
    browser_id = user_db.Column(user_db.String(255))  # primary key
    utc_millisecs = user_db.Column(TIMESTAMP)  # primary key
    hashed_email = user_db.Column(user_db.String(255))
    page_path = user_db.Column(user_db.String(500))
    page_views = user_db.Column(user_db.Integer)
    page_value = user_db.Column(user_db.Float)
    sessions = user_db.Column(user_db.Integer)

    browser = user_db.Column(user_db.String(255))
    browser_size = user_db.Column(user_db.String(255))
    operating_system = user_db.Column(user_db.String(255))
    device_category = user_db.Column(user_db.String(255))
    mobile_device_branding = user_db.Column(user_db.String(255))
    mobile_device_model = user_db.Column(user_db.String(255))

    country = user_db.Column(user_db.String(255))
    region = user_db.Column(user_db.String(255))
    metro = user_db.Column(user_db.String(255))
    city = user_db.Column(user_db.String(255))
    latitude = user_db.Column(user_db.Float)
    longitude = user_db.Column(user_db.Float)

    events = relationship(Event, backref='web_tracking_page_view',
                          primaryjoin='WebTrackingPageView.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


class WebTrackingEcomm(user_db.Model):
    __tablename__ = 'web_tracking_ecomm'
    id = user_db.Column(user_db.Integer, primary_key=True)
    browser_id = user_db.Column(user_db.String(255))  # primary key
    utc_millisecs = user_db.Column(TIMESTAMP)  # primary key
    hashed_email = user_db.Column(user_db.String(255))
    total_value = user_db.Column(user_db.Float)
    item_quantity = user_db.Column(user_db.Integer)
    product_detail_views = user_db.Column(user_db.Integer)

    browser = user_db.Column(user_db.String(255))
    browser_size = user_db.Column(user_db.String(255))
    operating_system = user_db.Column(user_db.String(255))
    device_category = user_db.Column(user_db.String(255))
    mobile_device_branding = user_db.Column(user_db.String(255))
    mobile_device_model = user_db.Column(user_db.String(255))

    country = user_db.Column(user_db.String(255))
    region = user_db.Column(user_db.String(255))
    metro = user_db.Column(user_db.String(255))
    city = user_db.Column(user_db.String(255))
    latitude = user_db.Column(user_db.Float)
    longitude = user_db.Column(user_db.Float)

    events = relationship(Event, backref='web_tracking_ecomm',
                          primaryjoin='WebTrackingEcomm.id==Event.rec_id',
                          foreign_keys=[Event.rec_id],
                          passive_deletes='all')


class Customer(user_db.Model):
    __tablename__ = 'customer'
    id = user_db.Column(user_db.Integer, primary_key=True)
    customer_id = user_db.Column(user_db.String(255), unique=True)
    email_address = user_db.Column(user_db.String(255))
    hashed_email = user_db.Column(user_db.String(255))
    fname = user_db.Column(user_db.String(255))
    lname = user_db.Column(user_db.String(255))
    marketing_allowed = user_db.Column(user_db.Boolean)
    created_at = user_db.Column(TIMESTAMP)
    purchase_count = user_db.Column(user_db.Integer)
    total_spent_so_far = user_db.Column(user_db.Float)
    _last_updated = user_db.Column(TIMESTAMP)
    _last_ext_sync = user_db.Column(TIMESTAMP)
    city = user_db.Column(user_db.String(255))
    state = user_db.Column(user_db.String(255))
    interest_area = user_db.Column(user_db.String(255))
    status = user_db.Column(user_db.String(255))
    source = user_db.Column(user_db.String(255))
    last_communication = user_db.Column(TIMESTAMP)
    sales_rep = user_db.Column(user_db.String(255))

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


@user_db.event.listens_for(Customer, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created_at = datetime.datetime.utcnow()
    target.hashed_email = base64.b64encode(hmac.new(HASH_SECRET,
                                                    msg=target.email_address.encode('utf-8'),
                                                    digestmod=hashlib.sha256).digest()).hex()
    return target


@user_db.event.listens_for(Customer, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target._last_updated = datetime.datetime.utcnow()
    return target


class Upload(user_db.Model):
    __tablename__ = 'upload'
    name = user_db.Column(user_db.String(200), primary_key=True)
    image = user_db.Column(user_db.LargeBinary)
    last_modified = user_db.Column(TIMESTAMP)
    created = user_db.Column(TIMESTAMP)
    esp_hosted_url = user_db.Column(user_db.String(255))
    esp_hosted_key = user_db.Column(user_db.String(255))
    esp_hosted_id = user_db.Column(user_db.String(255))
    esp_hosted_category_id = user_db.Column(user_db.String(255))
    image_size_height = user_db.Column(user_db.Integer)
    image_size_width = user_db.Column(user_db.Integer)


@user_db.event.listens_for(Upload, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    return target


@user_db.event.listens_for(Upload, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target


class Template(user_db.Model):
    __tablename__ = 'template'
    key = user_db.Column(user_db.String(10), primary_key=True)
    name = user_db.Column(user_db.String(200), nullable=False)
    html = user_db.Column(TEXT)
    last_modified = user_db.Column(TIMESTAMP)
    created = user_db.Column(TIMESTAMP)
    template_data = user_db.Column(JSON(astext_type=Text()))
    meta_data = user_db.Column(JSON(astext_type=Text()))

    def get_key(self, name=None):
        if name is None:
            name = self.name
        return abs(hash(name)) % (10 ** 7)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.key)


@user_db.event.listens_for(Template, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    target.key = hashlib.md5(target.name.encode()).hexdigest()[0:7]
    return target


@user_db.event.listens_for(Template, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target


class Report(user_db.Model):
    __tablename__ = 'report'
    id = user_db.Column(user_db.Integer, primary_key=True)
    name = user_db.Column(user_db.String(255))
    table = user_db.Column(user_db.String(255))
    grp_by_first = user_db.Column(user_db.String(255))
    grp_by_second = user_db.Column(user_db.String(255))
    aggregate_op = user_db.Column(user_db.String(255))
    aggregate_field = user_db.Column(user_db.String(255))
    graph_type = user_db.Column(user_db.String(255))
    filters_json = user_db.Column(JSON(astext_type=Text()))
    created = user_db.Column(TIMESTAMP)
    last_modified = user_db.Column(TIMESTAMP)


@user_db.event.listens_for(Report, 'before_insert', retval=True)
def on_update(mapper, connection, target):
    target.created = datetime.datetime.utcnow()
    return target


@user_db.event.listens_for(Report, 'before_update', retval=True)
def on_update(mapper, connection, target):
    target.last_modified = datetime.datetime.utcnow()
    return target

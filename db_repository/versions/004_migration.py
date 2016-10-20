from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
send_job = Table('send_job', post_meta,
    Column('SendID', Integer, primary_key=True, nullable=False),
    Column('SchedTime', String(length=255)),
    Column('SentTime', String(length=255)),
    Column('EmailName', String(length=64)),
    Column('Subject', String(length=1024)),
    Column('PreviewURL', String(length=1024)),
)

eml_open = Table('eml_open', post_meta,
    Column('SendID', Integer),
    Column('SubscriberKey', String(length=255), primary_key=True, nullable=False),
    Column('EmailAddress', String(length=255)),
    Column('EventDate', String(length=255), primary_key=True, nullable=False),
    Column('TriggeredSendExternalKey', String(length=255)),
    Column('IsUnique', String(length=255)),
    Column('IpAddress', String(length=255)),
    Column('Country', String(length=255)),
    Column('Region', String(length=255)),
    Column('City', String(length=255)),
    Column('Latitude', String(length=255)),
    Column('Longitude', String(length=255)),
    Column('MetroCode', String(length=255)),
    Column('AreaCode', String(length=255)),
    Column('Browser', String(length=255)),
    Column('EmailClient', String(length=255)),
    Column('OperatingSystem', String(length=255)),
    Column('Device', String(length=255)),
)

eml_click = Table('eml_click', post_meta,
    Column('SendID', Integer),
    Column('SubscriberKey', String(length=255), primary_key=True, nullable=False),
    Column('EmailAddress', String(length=255)),
    Column('EventDate', String(length=255), primary_key=True, nullable=False),
    Column('SendURLID', String(length=255)),
    Column('URLID', String(length=255)),
    Column('URL', String(length=1024)),
    Column('Alias', String(length=255)),
    Column('TriggeredSendExternalKey', String(length=255)),
    Column('IsUnique', String(length=255)),
    Column('IpAddress', String(length=255)),
    Column('Country', String(length=255)),
    Column('Region', String(length=255)),
    Column('City', String(length=255)),
    Column('Latitude', String(length=255)),
    Column('Longitude', String(length=255)),
    Column('MetroCode', String(length=255)),
    Column('AreaCode', String(length=255)),
    Column('Browser', String(length=255)),
    Column('EmailClient', String(length=255)),
    Column('OperatingSystem', String(length=255)),
    Column('Device', String(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['send_job'].columns['SchedTime'].create()
    post_meta.tables['send_job'].columns['SentTime'].create()
    post_meta.tables['eml_open'].columns['EventDate'].create()
    post_meta.tables['eml_open'].columns['SubscriberKey'].create()
    post_meta.tables['eml_click'].columns['EventDate'].create()
    post_meta.tables['eml_click'].columns['SubscriberKey'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['send_job'].columns['SchedTime'].drop()
    post_meta.tables['send_job'].columns['SentTime'].drop()
    post_meta.tables['eml_open'].columns['EventDate'].drop()
    post_meta.tables['eml_open'].columns['SubscriberKey'].drop()
    post_meta.tables['eml_click'].columns['EventDate'].drop()
    post_meta.tables['eml_click'].columns['SubscriberKey'].drop()

from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eml_click = Table('eml_click', pre_meta,
    Column('SendID', INTEGER),
    Column('SubscriberKey', VARCHAR(length=255), primary_key=True, nullable=False),
    Column('EmailAddress', VARCHAR(length=255)),
    Column('SendURLID', VARCHAR(length=255)),
    Column('URLID', VARCHAR(length=255)),
    Column('URL', VARCHAR(length=1024)),
    Column('Alias', VARCHAR(length=255)),
    Column('TriggeredSendExternalKey', VARCHAR(length=255)),
    Column('IsUnique', VARCHAR(length=255)),
    Column('IpAddress', VARCHAR(length=255)),
    Column('Country', VARCHAR(length=255)),
    Column('Region', VARCHAR(length=255)),
    Column('City', VARCHAR(length=255)),
    Column('Latitude', VARCHAR(length=255)),
    Column('Longitude', VARCHAR(length=255)),
    Column('MetroCode', VARCHAR(length=255)),
    Column('AreaCode', VARCHAR(length=255)),
    Column('Browser', VARCHAR(length=255)),
    Column('EmailClient', VARCHAR(length=255)),
    Column('OperatingSystem', VARCHAR(length=255)),
    Column('Device', VARCHAR(length=255)),
    Column('EventDateDate', TIMESTAMP),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eml_click'].columns['EventDateDate'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eml_click'].columns['EventDateDate'].create()

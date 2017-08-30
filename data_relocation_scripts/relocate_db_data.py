"""
    Adjust TABLES variable to select which tables to COPY
    NOTE: Alternative & much faster version of data migration is commented out at the bottom of this module
"""

# SQLAlchemy Migration Method ~10 minutes for 2 million recs
from sqlalchemy.orm import make_transient
from sqlalchemy.exc import IntegrityError

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from server.app.common.models.user_models import Purchase, EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, \
    Customer, WebTrackingPageView, WebTrackingEvent, EventDefinition, Event, Report

# Tables to copy
TABLES = [EmlOpen, EmlClick, EmlSend, WebTrackingEcomm, WebTrackingPageView, WebTrackingEvent,
          EventDefinition, Event, Report, Purchase, Customer]

# Target Database
hostname = 'postgres-dev.cdwkdjoq5xbu.us-east-2.rds.amazonaws.com'
username = 'bluenilesw'
db_name = 'test_migration'
port = '5432'
password = 'BlueNileSW123!'

# Source Database
source_hostname = 'ec2-34-197-30-128.compute-1.amazonaws.com'
source_username = 'u89oulkeem82k9'
source_db_name = 'dbvlecm2t0g7lm'
source_port = '5432'
source_password = 'p57c3fb6eef9d031a6bf9389286db6b7fe605a1b045265cd4c6aa8ddc884d5fad'

batch_size = 20000

# dialect+driver://username:password@host:port/database
target_db_engine = create_engine(f'postgresql://{username}:{password}@{hostname}:{port}/{db_name}')
target_session = scoped_session(sessionmaker(bind=target_db_engine))()

source_db_engine = create_engine('postgresql://'
                                 f'{source_username}:{source_password}@{source_hostname}:{source_port}/{source_db_name}'
                                 )
source_session = scoped_session(sessionmaker(bind=source_db_engine))()

for a_table in TABLES:
    print('Migrating {0}...'.format(a_table.__name__))
    num_recs = source_session.query(a_table).count()
    if num_recs == 0:
        print ('No records for table {0}'.format(a_table.__name__))
        continue

    batches=int(num_recs/batch_size)
    rem = num_recs%batch_size

    print('Found {0} records to migrate '.format(num_recs))
    print('Batches: {0}, remainder: {1}'.format(batches, rem))

    if batches > 0:
        i = 0
        for i in range(batches):
            print(f'Processing {i*batch_size} through {(i+1)*batch_size}')

            all_items = source_session.query(a_table).order_by(a_table.id).slice(i*batch_size, (i+1)*batch_size)
            for row in all_items:
                source_session.expunge(row)
                make_transient(row)
                target_session.add(row)
            try:
                target_session.commit()
            except IntegrityError as exc:
                print('Integrity Error: table: {0}, batch: {1}:{2}'.format
                      (a_table.__name__, i*batch_size, (i+1)*batch_size))
                target_session.rollback()

        print(f'Processing{(i+1)*batch_size} through {(i+1)*batch_size+rem}')
        all_items = source_session.query(a_table).order_by(a_table.id).slice((i+1)*batch_size, (i+1)*batch_size+rem)
        for row in all_items:
            source_session.expunge(row)
            make_transient(row)
            target_session.add(row)
        try:
            target_session.commit()
        except IntegrityError as exc:
            print('Integrity Error: table: {0}, batch: {1}:{2}'.format
                  (a_table.__name__, (i+1)*batch_size, (i+1)*batch_size+rem))
            target_session.rollback()

    else:
        all_items = source_session.query(a_table).all()
        for row in all_items:
            source_session.expunge(row)
            make_transient(row)
            target_session.add(row)
        try:
            target_session.commit()
        except IntegrityError as exc:
            print('Integrity Error for the ENTIRE Table: table: {0}'.format(a_table.__name__))
            target_session.rollback()

    print('Done Migrating {0}'.format(a_table.__name__))
    print()


"""
# Alternative Migration Method ~32 seconds for 2 million recs
# Target Database
hostname = 'postgres-dev.cdwkdjoq5xbu.us-east-2.rds.amazonaws.com'
username = 'bluenilesw'
db_name = 'test_migration'
port = '5432'
password = 'BlueNileSW123!'

# Source Database
source_hostname = 'ec2-34-197-30-128.compute-1.amazonaws.com'
source_username = 'u89oulkeem82k9'
source_db_name = 'dbvlecm2t0g7lm'
source_port = '5432'
source_password = 'p57c3fb6eef9d031a6bf9389286db6b7fe605a1b045265cd4c6aa8ddc884d5fad'

#Tables to Copy
TABLES = ['web_tracking_ecomm', 'web_tracking_event', 'web_tracking_page_view',
          'template', 'upload', 'customer', 'eml_click', 'eml_open', 'eml_send',
          'event', 'event_def', 'purchase', 'report', 'send_job']

import psycopg2
from io import BytesIO

source_con = psycopg2.connect(database=source_db_name, user=source_username,
                              password=source_password, host=source_hostname, port=source_port)
source = source_con.cursor()

target_connection = psycopg2.connect(database=db_name, user=username, password=password, host=hostname, port=port)
target = target_connection.cursor()

data_input = BytesIO()

for a_table in TABLES:
    try:
        print(f'Migrating {a_table} table')
        source.copy_expert(f'COPY (select * from {a_table}) TO STDOUT', data_input)
        data_input.seek(0)
        target.copy_expert(f'COPY {a_table} FROM STDOUT', data_input)
        target_connection.commit()
        print(f'Table {a_table} successfully migrated')
    except Exception:
        print(f'ERROR migrating {a_table} table')

    print()
"""
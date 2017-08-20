""" Define accounts and users for application db setup migration
    CAUTION: do not run this script until you understand what it does
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import create_database

from server.app.common.models.system_models import system_db, ClientAccount, UserPermissions
from server.app.common.models.user_models import user_db

hostname = 'postgres-dev.cdwkdjoq5xbu.us-east-2.rds.amazonaws.com'
username = 'bluenilesw'
db_name = 'system_db'
port = '5432'
password = 'BlueNileSW123!'

# dialect+driver://username:password@host:port/database
system_db_engine = create_engine(f'postgresql://{username}:{password}@{hostname}:{port}/{db_name}')
system_db.metadata.create_all(system_db_engine)
system_session = scoped_session(sessionmaker(bind=system_db_engine))()

# Define accounts and users
accounts = ['test_account']
# accounts = ['Galileo', 'test_account']
users = ('vitalik301@gmail.com', 'val.petrov@gmail.com', 'bernt@bluenilesw.com')

for account_name in accounts:
    account_db_uri = f'postgresql://{username}:{password}@{hostname}:{port}/{name.lower()}'
    try:
        print(f'Creating postgres catalogue for {account_name} account')
        create_database(account_db_uri)
    except Exception:
        print(f'Could not create db for {account_name} account')
        continue

    print(f'Creating system entries for {account_name}')
    account = ClientAccount(account_name=account_name, database_uri=account_db_uri)
    print(f'Adding account: {account_name} to system_db')
    for a_user in users:
        print(f'Adding user {a_user} to system_db')
        user = UserPermissions(username=a_user, role='admin')
        account.permissions.append(user)
        system_session.add(user)

    system_session.add(account)
    system_session.commit()

    print(f'Creating tables for {account_name}...')
    user_db_engine = create_engine(account_db_uri)
    user_db.metadata.create_all(user_db_engine)
    print(f'Done creating tables for {account_name}')
    print()


print('Successfully created system entries and tables for all accounts')

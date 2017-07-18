from server.app.common.models.system_models import system_session, ClientAccount, UserPermissions
from server.app.common.models.user_models import user_db


class AccountCreationService:
    def __init__(self, account_name, admin_user):
        self.admin_user = admin_user
        self.account_name = account_name

    def execute(self):
        userdb_uri = self.create_postgres(self.account_name, user_db)
        if userdb_uri is None:
            raise Exception("Cannot create database {0}".format(self.account_name))
        self.create_mongo(self.account_name)
        self.init_system_entries(self.account_name, userdb_uri, self.admin_user)

    @staticmethod
    def init_system_entries(name, uri, username='vitalik301@gmail.com'):
        local_session = system_session()

        account = ClientAccount(account_name=name, database_uri=uri)
        user = UserPermissions(username=username, role='admin')
        account.permissions.append(user)

        local_session.add(user)
        local_session.add(account)
        local_session.commit()

    @staticmethod
    def create_postgres(name, db_model):
        try:
            import sqlalchemy_utils
            from sqlalchemy import create_engine

            # TODO: don't hardcode this, obviously
            db_uri = 'postgresql://localhost/{0}'.format(name)

            # create default db
            if sqlalchemy_utils.database_exists(db_uri):
                #sqlalchemy_utils.drop_database(db_uri)
                return None
            sqlalchemy_utils.create_database(db_uri)

            # create tables
            engine = create_engine(db_uri)
            db_model.metadata.create_all(engine)

            return db_uri

        except Exception as ex:
            print(str(ex))
            return None

    @staticmethod
    def create_mongo(name):
        return True

from server.app.common.models.system_models import session_scope
from server.app.common.models.system_models import ClientAccount, UserPermissions
from server.app.common.models.user_models import user_db


class AccountCreationService:
    def __init__(self, account_name, admin_user, config=None):
        self.admin_user = admin_user
        self.account_name = account_name
        self.config = config

    def execute(self):
        userdb_uri = self.create_postgres(self.account_name, user_db)
        if userdb_uri is None:
            raise Exception("Cannot create database {0}".format(self.account_name))
        self.create_mongo(self.account_name)
        self.init_system_entries(self.account_name, userdb_uri, self.admin_user)

    def delete_account(self, mongo=None):
        import sqlalchemy_utils

        # Eliminate system_db entries
        with session_scope() as db_session:
            account = db_session.query(ClientAccount).filter(ClientAccount.account_name == self.account_name).first()
            db_session.delete(account)

        # Demolish postgres
        db_uri = AccountCreationService.get_postgres_uri(self.account_name)
        if sqlalchemy_utils.database_exists(db_uri):
            sqlalchemy_utils.drop_database(db_uri)

        # Eradicate mongo collections
        if mongo is not None:
            for a_collection_name in mongo.db.collection_names():
                if a_collection_name.endswith(self.account_name):
                    print('dropping collection: ', a_collection_name)
                    mongo.db[a_collection_name].drop()

    @staticmethod
    def init_system_entries(name, db_uri, username='vitalik301@gmail.com'):

        with session_scope() as db_session:
            account = ClientAccount(account_name=name, database_uri=db_uri)
            user = UserPermissions(username=username, role='admin')
            account.permissions.append(user)

            db_session.add(user)
            db_session.add(account)

    def create_postgres(self, name, db_model):
        try:
            import sqlalchemy_utils
            from sqlalchemy import create_engine

            db_uri = AccountCreationService.get_postgres_uri(name)

            # create default db
            if sqlalchemy_utils.database_exists(db_uri):
                # Drop database call could be more appropriate
                # However, it could lead to (accidental) data loss of an entire catalog
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

    @staticmethod
    def get_postgres_uri(account_name):
        return 'postgresql://bluenilesw:BlueNileSW123!@postgres-dev.cdwkdjoq5xbu.us-east-2.rds.amazonaws.com:5432/' \
               + account_name

from server.app.common.models.system_models import session_scope
from server.app.common.models.system_models import ClientAccount, UserPermissions
from server.app.common.models.user_models import user_db


class AccountCreationService:
    def __init__(self, account_name, admin_user, config):
        self.config = config
        self.admin_user = admin_user
        self.account_name = account_name

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
            db_session.commit()
            db_session.close()

        # Demolish postgres
        db_uri, db_uri_env = AccountCreationService.get_postgres_uri(self.account_name)
        if sqlalchemy_utils.database_exists(db_uri):
            # TODO: reinstate drop_database call
            pass
            # sqlalchemy_utils.drop_database(db_uri)

        # Eradicate mongo collections
        if mongo is not None:
            for a_collection_name in mongo.db.collection_names():
                if a_collection_name.endswith(self.account_name):
                    print('dropping collection: ', a_collection_name)
                    mongo.db[a_collection_name].drop()

    @staticmethod
    def init_system_entries(name, uri_env, username='vitalik301@gmail.com'):

        with session_scope() as db_session:
            account = ClientAccount(account_name=name, database_uri=uri_env)
            user = UserPermissions(username=username, role='admin')
            account.permissions.append(user)

            db_session.add(user)
            db_session.add(account)
            db_session.commit()


# TODO: support on heroku devbox... current version only supports local version
    def create_postgres(self, name, db_model):
        try:
            import sqlalchemy_utils
            from sqlalchemy import create_engine

            db_uri, db_uri_env = AccountCreationService.get_postgres_uri(name)

            # create default db
            # TODO: rewrite this logic for heroku --> db_uri format not supported on sqlalchemy
            if sqlalchemy_utils.database_exists(db_uri):
                # Drop database call could be more appropriate
                # However, it could lead to accidental data loss of the entire catalog
                return None
            sqlalchemy_utils.create_database(db_uri)
            #TODO: create env var
            self.config[db_uri_env] = db_uri

            # create tables
            # TODO: rewrite this logic for heroku --> db_uri format not supported on sqlalchemy
            engine = create_engine(db_uri)
            db_model.metadata.create_all(engine)

            return db_uri_env

        except Exception as ex:
            print(str(ex))
            return None

    @staticmethod
    def create_mongo(name):
        return True

    @staticmethod
    def get_postgres_uri(account_name):
        db_uri_env = account_name.upper() + '_URL'
        db_uri = 'postgresql://localhost/' + account_name
        return db_uri, db_uri_env

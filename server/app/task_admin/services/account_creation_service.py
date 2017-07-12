from server.app.common.models.system_models import system_db, ClientAccount, UserPermissions
from server.app.common.models.user_models import user_db


class AccountCreationService:
    def __init__(self, account_name):
        self.account_name = account_name

    def execute(self):
        uri = self.create_postgres(self.account_name, user_db)
        self.create_mongo(self.account_name)
        self.init_system_entries(self.account_name, uri)

    @staticmethod
    def init_system_entries(name, uri, username='vitalik301@gmail.com'):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # an Engine, which the Session will use for connection
        # resources

        # TODO: this will be injected once the old SQLAlchemy session creation is refactored per user
        engine = create_engine('postgresql://localhost/bluenile')

        # create a configured "Session" class
        local_session = sessionmaker(bind=engine)()

        account = ClientAccount(account_name=name)
        user = UserPermissions(database_uri=uri, username=username, role='admin')
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
                sqlalchemy_utils.drop_database(db_uri)
            sqlalchemy_utils.create_database(db_uri)

            # create tables
            engine = create_engine(db_uri)
            print("----User db session")
            print(db_model.session)
            db_model.metadata.create_all(engine)

            return db_uri

        except Exception as ex:
            print(str(ex))
            return None

    @staticmethod
    def create_mongo(name):
        return True

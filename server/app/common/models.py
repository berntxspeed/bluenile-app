from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class KeyValue(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255))

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

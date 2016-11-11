from flask_pymongo import PyMongo
from celery import Celery


def provide_mongo():
    return PyMongo()


def provide_celery(app):
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    return celery

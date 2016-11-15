from flask_pymongo import PyMongo
from celery import Celery


def provide_mongo():
    return PyMongo()


def provide_celery(app):
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], include='server.app.common.workers.module')
    print('Celery broker: ', app.config['CELERY_BROKER_URL'])
    print('Celery name: ', app.name)
    celery.conf.update(app.config)

    return celery

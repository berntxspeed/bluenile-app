from flask_pymongo import PyMongo
from celery import Celery


def provide_mongo():
    return PyMongo()


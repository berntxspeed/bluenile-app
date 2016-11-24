from flask_pymongo import PyMongo


def provide_mongo():
    return PyMongo()


from sqlalchemy.orm.exc import NoResultFound
from flask import Request, jsonify
from injector import inject

from . import main
from ..common.models import KeyValue
from ..injector_keys import SQLAlchemy

@main.route('/<key>')
def get(key):
    try:
        kv = KeyValue.query.filter_by(key=key).one()
    except NoResultFound:
        response = jsonify(status='No such key', context=key)
        response.status = '404 Not Found'
        return response
    return jsonify(key=kv.key, value=kv.value)

# how would i get cache'ing here without invoking inject (since injectors not built yet?)
# @cached(timeout=1)
@main.route('/')
def list():
    data = [i.key for i in KeyValue.query.order_by(KeyValue.key)]
    return jsonify(keys=data)

@main.route('/', methods=['POST'])
@inject(request=Request, db=SQLAlchemy)
def create(request, db):
    kv = KeyValue(key=request.form['key'], value=request.form['value'])
    db.session.add(kv)
    db.session.commit()
    response = jsonify(status='OK')
    response.status = '201 CREATED'
    return response

@main.route('/<key>', methods=['DELETE'])
@inject(db=SQLAlchemy)
def delete(db, key):
    KeyValue.query.filter_by(key=key).delete()
    db.session.commit()
    response = jsonify(status='OK')
    response.status = '200 OK'
    return response

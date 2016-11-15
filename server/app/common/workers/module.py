# import injector

# from celery import shared_task
# from celery.task import task
# from flask import Flask
# from injector import Module, inject
#
# from manage import injector
# from ...stats.injector_keys import DataLoadServ

# app = injector.get(Flask)

from manage import celery, injector
from ...stats.injector_keys import DataLoadServ


@celery.task
def load():
    service = injector.get(DataLoadServ)
    service.load_customers()

# class CustomersTask(Task):
#     def run(self, *args, **kwargs):
#         service = injector.get(DataLoadServ)
#         service.load_customers()

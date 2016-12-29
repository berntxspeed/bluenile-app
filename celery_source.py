from server.app import create_app

celery_app = create_app()


def provide_celery(app=celery_app):
    from celery import Celery
    instance = Celery(app.name, broker=app.config['CELERY_BROKER_URL'],
                      backend=app.config['CELERY_BROKER_URL'],
                      include=['server.app.stats.workers',
                               'server.app.auth.workers',
                               'server.app.data.workers'])
    instance.conf.update(app.config)

    return instance


celery = provide_celery()

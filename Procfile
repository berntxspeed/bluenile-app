web: gunicorn manage:app -b 0.0.0.0:$PORT -w 3 --log-file -
worker: celery worker --app=manage.celery

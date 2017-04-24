web: gunicorn manage:app -b 0.0.0.0:$PORT -w 3 --log-file -
worker1: celery worker --app=manage.celery -B
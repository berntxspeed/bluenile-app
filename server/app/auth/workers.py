from manage import celery

app = celery

@app.task
def auth_task():
    pass

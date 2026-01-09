import os
from celery import Celery

# Initialize Celery application
celery = Celery(
    "worker",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)

# Add some configurations
celery.conf.update(
    task_ignore_result=False,
    result_expires=3600,
    broker_connection_retry_on_startup=True
)

# Initial Celery task discovery
celery_routes = ["app.celery_tasks"]

# Include testing tasks if in testing environment
if os.getenv("FLASK_ENV") == "testing":
    celery_routes.append("tests.task_creation.celery_tasks")

celery.autodiscover_tasks(celery_routes, related_name='', force=True)
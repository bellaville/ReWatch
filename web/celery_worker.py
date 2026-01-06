import os
from celery_app import celery

# For discovering tasks in both the main app and test modules
# Required to be seperated from celery_app to avoid circular imports

celery_routes = ["app.celery_tasks"]

if os.getenv("FLASK_ENV") == "testing":
    celery_routes.append("tests.task_creation.celery_tasks")

celery.autodiscover_tasks(celery_routes, force=True)
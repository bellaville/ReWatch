from celery import Celery
import os
from flask import Flask

from app import create_app

def create_celery(app: Flask) -> Celery:
    """
    Create a Celery instance and tie it to the Flask app context.

    Args:
        app: The Flask application instance.

    Returns:
        Celery: Configured Celery instance.
    """
    celery = Celery(
        app.import_name,
        broker=os.environ["REDIS_URL"],
        backend=os.environ["REDIS_URL"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs) 
               
    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = create_celery(flask_app)
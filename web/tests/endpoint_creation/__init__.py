from flask import Flask

from .test_accel import accel_test
from .test_injectable_interfaces import injection_test
from .celery_endpoints import celery_test

def register_testing_endpoints(app: Flask) -> None:
    if app.debug or app.config["TESTING"]:
        app.register_blueprint(accel_test)
        app.register_blueprint(injection_test)
        app.register_blueprint(celery_test)
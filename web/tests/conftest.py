import os
import pytest
from run import create_app

# Based off example at: https://testdriven.io/blog/flask-pytest/

@pytest.fixture(scope='module')
def test_client():
    # Set the Testing configuration prior to creating the Flask application
    flask_app = create_app(test_config=True)

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client
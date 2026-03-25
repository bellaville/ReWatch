import pytest

from run import create_app

# Based off example at: https://testdriven.io/blog/flask-pytest/

@pytest.fixture(scope='module')
def test_app():
    # Set the Testing configuration prior to creating the Flask application
    flask_app = create_app(test_config=True)
    
    # Add testing endpoints
    from tests.endpoint_creation import register_testing_endpoints
    register_testing_endpoints(flask_app)

    yield flask_app

@pytest.fixture(scope='function')
def test_client(test_app):
    # Create a test client using the Flask application configured for testing
    with test_app.test_client() as testing_client:
        with test_app.app_context():
            yield testing_client
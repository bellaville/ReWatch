import pytest
import os
import shutil
from flask.testing import FlaskClient

RESULTS_DIR = './../endpoint_creation/accel_results'

@pytest.fixture(autouse=True)
def clean_results_dir():
    """
    Fixture to clean up the acceleration results directory before and after tests.
    Ensures a fresh state for each test run.
    """    
    # Clean up before test
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
        
    yield
    
    # Clean up after test
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)

def post_example_data(test_client: FlaskClient):
    """
    Helper function to post example acceleration data.
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    example_json = {
        "ts": 12321233232,
        "data": [
            {
                "ts": 12321233233,
                "x": 1,
                "y": 1,
                "z": 1
            }
        ]
    }
    response = test_client.post('/test/debug/accel', json=example_json)
    return response

def test_getting_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN adding data, then requesting the acceleration data archive
    THEN a ZIP file containing the data is returned
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    # Ensure there is at least one file to zip
    post_example_data(test_client)
    response = test_client.get('/test/debug/accel')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
    assert 'attachment; filename=accel_data_archive.zip' in response.headers['Content-Disposition']
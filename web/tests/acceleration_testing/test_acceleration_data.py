from flask.testing import FlaskClient
import pytest

from app.models import AssessmentStageData, PatientAssessment
from app.db import db

@pytest.fixture(scope='function')
def wipe_acceleration_data(test_client: FlaskClient):
    """
    Fixture to wipe acceleration test data before each test.
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    db.session.query(AssessmentStageData).delete()
    db.session.commit()
    
    yield
    
    db.session.query(AssessmentStageData).delete()
    db.session.commit()

@pytest.fixture(scope='function', autouse=True)
def create_assessment(test_client: FlaskClient):
    """
    Fixture to create a PatientAssessment entry before each test.
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    new_assessment = PatientAssessment(
        patient_id=1,
        score=0,
        avg_reaction_time=1200,
        total_rounds=3,
        difficulty="easy"
    )

    db.session.add(new_assessment)
    db.session.commit()


def post_example_data(test_client: FlaskClient):
    """
    Helper function to post example acceleration data.
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    example_json = {
        "ts": 12321233232,
        "assessmentID": 1,
        "stage": "gait",
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
    THEN the data is properly saved and returned.
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """
    post_example_data(test_client)
    response = test_client.get('/test/debug/accel')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["assessmentID"] == 1
    assert data[0]["stage"] == "gait"
    assert len(data[0]["data"]) == 1
    assert data[0]["data"][0]["x"] == 1
    assert data[0]["data"][0]["y"] == 1
    assert data[0]["data"][0]["z"] == 1
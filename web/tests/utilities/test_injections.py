from flask.testing import FlaskClient
import pytest

from app.db import db
from app.models import PatientAssessment, User

def fetch_user_data(user_id: int):
    """
    Helper function to fetch user data via DB.
    
    Args:
        user_id (int): ID of the user to fetch.
    """
    return db.session.get(User, user_id)

@pytest.fixture(scope='function')
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
    
    yield new_assessment.id

def test_posting_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with context injection
    THEN the user is properly loaded
    
    Args:
        test_client (FlaskClient): Flask test client used to send requests to the application.
    """   
    
    user = fetch_user_data(1)
    response = test_client.post('/test/1')
    response = response.get_json()
    
    assert response["userid"] == user.id
    assert response["email"] == user.email
    
    user = fetch_user_data(2)
    response = test_client.post('/test/2')
    response = response.get_json()
    
    assert response["userid"] == user.id
    assert response["email"] == user.email
    
def test_posting_unavailable_user_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with context injection with invalid ID
    THEN the proper 404 error is returned
    
    Args:
        test_client (FlaskClient): Flask test client used to send requests to the application.
    """   
    response = test_client.post('/test/-1')
    
    assert response.status_code == 404
    assert "The requested object was not found" in response.text
    
def test_posting_multiple_injections(test_client: FlaskClient, create_assessment):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with multiple context injections
    THEN the user and assessment are properly loaded
    
    Args:
        test_client (FlaskClient): Flask test client used to send requests to the application.
    """   
    
    user = fetch_user_data(1)
    response = test_client.post(f'/test/{create_assessment}/1')
    response = response.get_json()
    
    assert response["userid"] == user.id
    assert response["email"] == user.email
    assert response["assessment_id"] == create_assessment
 
def test_posting_unavailable_multiple_injection_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with multiple context injections with invalid assessment ID
    THEN the proper 404 error is returned
    
    Args:
        test_client (FlaskClient): Flask test client used to send requests to the application.
    """   
    response = test_client.post('/test/-1/1')
    
    assert response.status_code == 404
    assert "The requested object was not found" in response.text
    
    response = test_client.post('/test/1/-1')
    
    assert response.status_code == 404
    assert "The requested object was not found" in response.text
    
    
from flask.testing import FlaskClient

from app.db import db
from app.models import User

def fetch_user_data(user_id: int):
    """
    Helper function to fetch user data via DB.
    
    Args:
        test_client: Flask test client used to send requests to the application.
        user_id: ID of the user to fetch.
    """
    return db.session.get(User, user_id)

def test_posting_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with context injection
    THEN the user is properly loaded
    
    Args:
        test_client: Flask test client used to send requests to the application.
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
        test_client: Flask test client used to send requests to the application.
    """   
    response = test_client.post('/test/-1')
    
    assert response.status_code == 404
    assert "The requested object was not found" in response.text
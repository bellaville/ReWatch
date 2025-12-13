from flask.testing import FlaskClient

def test_posting_data(test_client: FlaskClient):
    """
    GIVEN a Flask test client
    WHEN posting to a URL with context injection
    THEN the user is properly loaded
    
    Args:
        test_client: Flask test client used to send requests to the application.
    """   
    response = test_client.post('/test/1')
    response = response.get_json()
    
    assert response["userid"] == 1
    
    response = test_client.post('/test/2')
    response = response.get_json()
    
    assert response["userid"] == 2
    
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
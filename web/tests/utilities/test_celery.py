import re

from flask.testing import FlaskClient

def test_celery_task_registration(test_client: FlaskClient):
    """
    GIVEN a Celery app
    WHEN an asynchronous task is defined
    THEN the ID of the task is returned
    """
    response = test_client.get('/test_celery/3/5')
    assert response.status_code == 200
    assert 'Task submitted. Result: ' in response.data.decode()

    UUID_PATTERN = re.compile(r'[a-f0-9\-]{36}')
    task_id = response.data.decode().split('Task submitted. Result: ')[1]
    assert UUID_PATTERN.match(task_id)
    
def test_celery_task_result_retrieval(test_client: FlaskClient):
    """
    GIVEN a Celery app
    WHEN a task result is requested by its ID
    THEN the result of the task is returned
    """
    first, second = 10, 15
    response = test_client.get(f'/test_celery/{first}/{second}')
    assert response.status_code == 200
    data = response.data.decode()
    assert 'Task submitted. Result: ' in data
    
    # Extract the result from the response
    result_value = data.split('Task submitted. Result: ')[1]
    
    # Use the result value to get the task result
    response = test_client.get('/test_celery/result/' + result_value)
    assert response.status_code == 200
    assert f'Task result: {first + second}' in response.data.decode()
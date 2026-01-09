import os
import time
from flask import Blueprint
from celery_worker import celery
from celery.result import AsyncResult

from tests.task_creation.celery_tasks import add

celery_test = Blueprint('celery_test', __name__)

@celery_test.route('/test_celery/<int:a>/<int:b>', methods=['GET'])
def test_celery(a: int, b: int):
    """
    Endpoint to test the Celery add task.

    Args:
        a (int): First integer to add.
        b (int): Second integer to add.

    Returns:
        str: Result of the addition as a string.
    """    
    result = add.delay(a, b)
    
    return f'Task submitted. Result: {result.id}'

@celery_test.route('/test_celery/result/<string:id>', methods=['GET'])
def get_celery_result(id: str):
    """
    Endpoint to get the result of a Celery task by its ID.

    Args:
        id (int): The task ID.

    Returns:
        str: The result of the task or its status.
    """
    result = AsyncResult(id, app=celery)

    # Wait for the task to complete or timeout after 10 seconds
    timeout = 10
    waited = 0
    while not result.ready() and waited < timeout:
        time.sleep(1)
        waited += 1
        
    if result.ready():
        return f'Task result: {result.result}'
    else:
        return f'Task is still processing or timed out after {timeout} seconds.'
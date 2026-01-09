from celery_worker import celery

@celery.task(name="add_task")
def add(x: int, y: int) -> int:
    """
    Celery task to add two numbers together.

    Args:
        x (int): First integer to add.
        y (int): Second integer to add.

    Returns:
        int: The sum of x and y.
    """
    return x + y
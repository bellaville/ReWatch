#!/bin/bash
# Start the Celery worker
celery -A celery_worker.celery worker --loglevel=info
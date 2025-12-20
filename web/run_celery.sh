#!/bin/bash
# Start the Celery worker in azure environment
exec celery -A celery_worker.celery worker --loglevel=info
#!/bin/bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting application..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 run:app

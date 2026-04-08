## Description
ReWatch is a proof-of-concept platform that pairs a WearOS smartwatch application with a Flask-based web application to monitor three key biomarkers: visual short-term memory, choice reaction time, and gait variability.

The web platform is where patients can register, carry out tests involving the smartwatch, and visually view test results.

Physicians can register on ReWatch, view assigned patients assessment history, assign new patients, and carry out assessments for patients.

## Setup

### Requirements

Docker is required for development of this project, or the creation of a third party celery worker with a redis instance.

### Third party apps

This projects requires the use of a Redis Key-Value store that is to be used by celery. See below for how to set it up it within the project. To start it, use `web/docker-compose.dev.yaml` to create the required docker containers, as well as setting the below `REDIS_URL` to `redis://redis:6379/0`. See below for relevant windows commands:
```
cd web
$env:REDIS_URL = "redis://localhost:6379/0"
docker compose -f docker-compose.dev.yaml up -d --build
```
For Mac users (macOS does not recognize redis as a hostname):
```
cd web
export REDIS_URL="redis://127.0.0.1:6379/0"
docker compose -f docker-compose.dev.yaml up -d --build
```

### Env. Vars

- `REDIS_URL`: URL For the Redis instance being utilized
- `FLASK_ENV`: Either `testing` or `production`

An `EnvironmentError` indicates that one or more of these haven't been set

### Running Tests

To run web tests, use the following commands:
```
cd web
python -m pytest
```

# Overall Setup of the WebApp
1. Download project file
2. Open Terminal (for Mac) or Command Prompt (for Windows)
3. Navigate to project directory
4. Execute the following commands based on your operating system:

For Windows
```
python -m venv .venv
.venv\Scripts\activate.bat
cd web
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest
set FLASK_ENV=development
set REDIS_URL=redis://127.0.0.1:6379/0
docker compose -f docker-compose.dev.yaml up -d --build
python run.py

```
For Mac
```
python3.11 -m venv venv
source venv/bin/activate
cd web
python3.11 -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest
export FLASK_APP=run.py
export FLASK_ENV=development
export REDIS_URL="redis://127.0.0.1:6379/0"
docker compose -f docker-compose.dev.yaml up -d
flask run
```
For Linux
```
cd web
sudo systemctl start docker
export FLASK_APP=run.py
export FLASK_ENV=development
export REDIS_URL="redis://127.0.0.1:6379/0"
docker compose -f docker-compose.dev.yaml up -d
flask run --host 0.0.0.0
```

## Web Libraries & Frameworks

### Celery

Celery is for the queuing and processing of background tasks. In this project, it will be a seperate thread working on data processing as required by the backend. These tasks can be worked on asynchronously and results can be returned as they are readied. This queue is maintained through a Redis instance.

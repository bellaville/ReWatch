## Description
ReWatchWeb is a web-based app which will be paired with the Samsung Galaxy Watch 7 to carry out a small set of cognitive tests meant to quickly and 
efficiently provide an indication of whether or not a patient shows any signs of cognitive decline or impairment.

The web platform is where patients can register, carry out tests involving the smartwatch, and view test results and notes from their physician.

Physicians can register on ReWatchWeb, as well as view patient test data, assing tests to patients, and make notes on patient results.

## Setup

### Requirements

Docker is required for development of this project, or the creation of a third party celery worker with a redis instance.

### Third party apps

This projects requires the use of a Redis Key-Value store that is to be used by celery. See below for how to set it up it within the project. To start it, use `web/docker-compose.dev.yaml` to create the required docker containers, as well as setting the below `REDIS_URL` to `redis://redis:6379/0`. See below for relevant windows commands:
```
cd web
docker compose up -d
$env:REDIS_URL = "redis://redis:6379/0"
```

### Env. Vars

- `REDIS_URL`: URL For the Redis instance being utilized
- `FLASK_ENV`: Either `testing` or `production`

An `EnvironmentError` indicates that one or more of these haven't been set

## Web Libraries & Frameworks

### Celery

Celery is for the queuing and processing of background tasks. In this project, it will be a seperate thread working on data processing as required by the backend. These tasks can be worked on asynchronously and results can be returned as they are readied. This queue is maintained through a Redis instance.
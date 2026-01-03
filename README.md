## Description
ReWatchWeb is a web-based app which will be paired with the Samsung Galaxy Watch 7 to carry out a small set of cognitive tests meant to quickly and 
efficiently provide an indication of whether or not a patient shows any signs of cognitive decline or impairment.

The web platform is where patients can register, carry out tests involving the smartwatch, and view test results and notes from their physician.

Physicians can register on ReWatchWeb, as well as view patient test data, assing tests to patients, and make notes on patient results.

## Setup

### Third party apps

This projects requires the use of a Redis Key-Value store that is to be used by celery. See below for how to use it within the project.

### Env. Vars

- `REDIS_URL`: URL For the Redis instance being utilized
- `FLASK_ENV`: Either `testing` or `production`
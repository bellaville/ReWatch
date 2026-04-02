from app.db import db
from app.config.seeding import *
from app import create_app

# This only needs to be run if you want seeded users added!

# Create the app, and load all seed information in
app = create_app()

with app.app_context():
    db.drop_all() # for development
    db.create_all()
    seed_roles()
    seed_users()
    seed_patient_assessments()

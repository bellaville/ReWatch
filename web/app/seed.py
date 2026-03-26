from app.db import db
from app.config.seeding import *
from app import create_app

# file to run the application, no configuration should be present
app = create_app()

with app.app_context():
    db.drop_all() # for development
    db.create_all()
    seed_roles()
    seed_users()
    seed_patient_assessments()

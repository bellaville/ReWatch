from werkzeug.security import generate_password_hash

from app.models import Role, User, Patient, Physician, PatientAssessment
from app.db import db
import random
from datetime import datetime, timedelta, timezone


def seed_roles():
    """
    Seeds the database with initial roles if they don't exist.
    This function must be called inside an app context.
    """
    if Role.query.count() == 0:
        roles = [
            Role(id=1, name='Patient'),
            Role(id=2, name='Physician')
        ]
        db.session.add_all(roles)
        db.session.commit()
        print("Roles seeded successfully!")

def seed_users():
    """
    Seeds the database with dummy users.
    Only adds a user if the email does not already exist.
    Must be called inside an app context.
    """

    # Get roles (assumes seed_roles() has already run)
    patient_role = Role.query.filter_by(name='Patient').first()
    physician_role = Role.query.filter_by(name='Physician').first()

    # create Physician user
    physician_user = User.query.filter_by(email="dr.stephen@avengers.com").first()
    if not physician_user:
        physician_user = User(
            email= "dr.stephen@avengers.com", 
            name= "Dr. Stephen Strange",
            password=generate_password_hash("password123")
        )
        physician_user.roles.append(physician_role)
        db.session.add(physician_user)
        db.session.flush()
    
    # double check that the physician profile exists
    physician_profile = physician_user.physician_profile
    if not physician_profile:
        physician_profile = Physician(user_id=physician_user.id)
        db.session.add(physician_profile)
        db.session.flush()

    # List of dummy users to seed
    dummy_users = [
        {"email": "clark@DC.com", "name": "Clark Kent", "password": "password123", "role": patient_role},
        {"email": "gwen@amazing.com", "name": "Gwen Stacy", "password": "password123", "role": patient_role},
        {"email": "peter@amazing.com", "name": "Peter Parker", "password": "password123", "role": patient_role}
    ]

    for u in dummy_users:
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=u["email"]).first()
        if not existing_user:
            new_user = User(
                email=u["email"],
                name=u["name"],
                password=generate_password_hash(u["password"])
            )
            # Assign role
            if u["role"]:
                new_user.roles.append(u["role"])

            db.session.add(new_user)
            db.session.flush() # db generated ID is assigned

            # create Patient Profile with assigned Physician
            patient_profile = Patient(user_id=new_user.id, physician_id=physician_profile.id)
            db.session.add(patient_profile)

    db.session.commit()
    print("Dummy users seeded successfully (duplicates skipped).")


def seed_patient_assessments():
    """
    Seeds the database with PatientAssessment data for each seeded patient
    """

    patients = Patient.query.all()

    if not patients:
        print("No patients found. Seed users first.")
        return
    
    for patient in patients:
        # Skip if patient already has assessments
        if patient.assessments:
            continue

        # Create 3-6 assessments per patient
        num_assessments = random.randint(3, 6)

        for i in range(num_assessments):
            reaction_records = []
            total_reaction_time = 0
            num_rounds = random.randint(10, 20)
            difficulty = random.choice(["Easy", "Hard"])

            for u in range(num_rounds):
                time = round(random.uniform(920, 4200), 2)
                num_shapes = random.randint(3,7)
                correct = random.choice([True, False])

                reaction_records.append({
                    "time": time,
                    "diffculty": difficulty,
                    "num_shapes": num_shapes,
                    "correct": correct,
                })
                total_reaction_time += time

            avg_reaction_time = round(total_reaction_time/num_rounds, 2)
            correct_reactions = [r for r in reaction_records if r["correct"]]
            score = len(correct_reactions)

            assessment = PatientAssessment(
                patient_id=patient.id,
                score=score,
                total_rounds=num_rounds,
                avg_reaction_time=avg_reaction_time,
                date_taken=datetime.now(timezone.utc) - timedelta(days=(num_assessments-i)*3),
                difficulty=difficulty,
                reaction_records=reaction_records,
            )
            db.session.add(assessment)
    
    db.session.commit()
    print("Patient assessments seeded successfully!")
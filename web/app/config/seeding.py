from werkzeug.security import generate_password_hash

from app.models import Role, User
from app import db


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

    # List of dummy users to seed
    dummy_users = [
        {"email": "clark@DC.com", "name": "Clark Kent", "password": "password123", "role": patient_role},
        {"email": "gwen@amazing.com", "name": "Gwen Stacy", "password": "password123", "role": patient_role},
        {"email": "dr.stephen@avengers.com", "name": "Dr. Stephen Strange", "password": "password123", "role": physician_role},
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

    db.session.commit()
    print("Dummy users seeded successfully (duplicates skipped).")
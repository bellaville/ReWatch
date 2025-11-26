from app.models import Role
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

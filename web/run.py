from app import create_app, db
from app.models import Role

app = create_app()

# create tables, insert roles into database
with app.app_context():
    db.drop_all()
    db.create_all()
    patient = Role(id=1, name='Patient')
    physician = Role(id=2, name='Physician')

    db.session.add(patient)
    db.session.add(physician)

    db.session.commit()
    print("Roles created successfully!")

if __name__ == "__main__":
    app.run(debug=True)


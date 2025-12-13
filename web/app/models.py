from flask_login import UserMixin
from .db import db

# association table for users and roles (many to many)
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

# model for user objects
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    
    # to be able to link Physician OR Patient profile to User
    patient_profile = db.relationship('Patient', backref='user', uselist=False)
    physician_profile = db.relationship('Physician', backref='user', uselist=False)
    
    # check if this user has a certain role
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

# model for roles
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

# model for physician profile
class Physician(db.Model):
    __tablename__ = 'physician'
    id = db.Column(db.Integer, primary_key=True)
    # every Physician corresponds to exactly one User entry
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    
    # one Physician can have many Patients
    patients = db.relationship('Patient', backref='physician', lazy=True)

# model for patient profile
class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True) # link to User
    # each Patient belongs to exactly 1 Physician
    physician_id = db.Column(db.Integer, db.ForeignKey('physician.id'))

# model for a patient's assessment
class PatientAssessment(db.Model):
    __tablename__ = 'patient_assessment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id')) # link to Patient
    score = db.Column(db.Integer)
    avg_reaction_time = db.Column(db.Float)
    total_rounds = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime, default=db.func.current_timestamp()) # track when test was completed

    # set relationship with Patient so that we can access the associated Patient object from PatientAssessment
    patient = db.relationship('Patient', backref='assessments')



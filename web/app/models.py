from flask_login import UserMixin
from . import db

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

    # check if this user has a certain role
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

# model for roles
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


# class PatientAssessment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # link to User
#     score = db.Column(db.Integer)
#     avg_reaction_time = db.Column(db.Float)
#     memorization_time = db.Column(db.Float)
#     total_rounds = db.Column(db.Integer)
#     num_shapes = db.Column(db.Integer)
#     difficulty = db.Column(db.String(10))
#     date_taken = db.Column(db.DateTime, default=db.func.current_timestamp()) # track when test was completed

#     # set relationship with Patient so that we can access the associated Patient object from PatientAssessment
#     user = db.relationship('User', backref='assessments')



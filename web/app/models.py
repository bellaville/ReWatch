from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import enum
from typing import Any
from flask_login import UserMixin
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db import db

PATIENT_ROLE = "Patient"
PHYSICIAN_ROLE = "Physician"

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
    age = db.Column(db.Integer)
    height = db.Column(db.Integer)
    gender = db.Column(db.String(80))
    weight = db.Column(db.Integer)

# model for a patient's assessment
class PatientAssessment(db.Model):
    __tablename__ = 'patientassessment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id')) # link to Patient
    score = db.Column(db.Integer)
    avg_reaction_time = db.Column(db.Float)
    total_rounds = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime, default=db.func.current_timestamp()) # track when test was completed

    # set relationship with Patient so that we can access the associated Patient object from PatientAssessment
    patient = db.relationship('Patient', backref='assessments')

    @property
    def local_date_taken(self):
        """
        Convert stored UTC timestamp to America/Toronto time
        """
        if not self.date_taken:
            return None
        
        eastern = ZoneInfo("America/Toronto")

        # if timezone not identifiedd, assume UTC
        if self.date_taken.tzinfo is None:
            utc_dt = self.date_taken.replace(tzinfo=timezone.utc)
        else:
            utc_dt = self.date_taken

        return utc_dt.astimezone(eastern)


class AssessmentStage(enum.Enum):
    GAIT = "gait"
    REACTION = "reaction"

class AssessmentStageData(db.Model):
    __tablename__ = 'assessmentstagedata'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('patientassessment.id'))
    stage = db.Column(db.Enum(AssessmentStage))
    points = db.relationship('StageDataPoint', backref='stage_data', cascade="all, delete-orphan")
    
    @classmethod
    def from_json(cls, json_data: dict[str, Any]) -> "AssessmentStageData":
        """
        Create an AssessmentStageData instance from JSON data.
        
        Args:
            json_data (dict[str, Any]): JSON data containing assessment stage information.
            
        Returns:
            AssessmentStageData: The created AssessmentStageData instance.
        """
        stage = AssessmentStage(json_data["stage"].lower())
        stage_data = cls(
            assessment_id=json_data["assessmentID"],
            stage=stage
        )
        
        for point in json_data["data"]:
            ts = datetime.fromtimestamp(point["ts"] / 1000.0)
            stage_data.points.append(StageDataPoint(
                timestamp=ts,
                x=point["x"],
                y=point["y"],
                z=point["z"]
            ))
            
        return stage_data
    
    def to_json(self) -> dict[str, Any]:
        """
        Convert the AssessmentStageData instance to JSON format.
        
        Returns:
            dict[str, Any]: JSON representation of the AssessmentStageData.
        """
        return {
            "assessmentID": self.assessment_id,
            "stage": self.stage.value,
            "data": [
                {
                    "ts": int(point.timestamp.timestamp() * 1000),
                    "x": point.x,
                    "y": point.y,
                    "z": point.z
                } for point in self.points
            ]
        }
        
class StageDataPoint(db.Model):
    __tablename__ = 'stagedatapoint'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('assessmentstagedata.id'))
    timestamp = db.Column(db.DateTime(timezone=True))
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)

########################################### event listeners ##############################################

# listens for new users and adds patient or physician profile based on user role
@event.listens_for(Session, "after_flush")
def create_profiles_for_new_users(session, flush_context):
    # go through instances that were added in this flush
    for obj in session.new:
        if isinstance(obj, User):
            # role names for this user (assuming roles are already attached)
            role_names = {r.name for r in obj.roles}

            # create patient profile if user has patient role and no profile yet
            if PATIENT_ROLE in role_names and obj.patient_profile is None:
                patient = Patient(user=obj)
                session.add(patient)

            # create physician profile if user has physician role and no profile yet
            if PHYSICIAN_ROLE in role_names and obj.physician_profile is None:
                physician = Physician(user=obj)
                session.add(physician)

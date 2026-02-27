from datetime import datetime, timezone, timedelta
import random
from zoneinfo import ZoneInfo
import enum
from typing import Any
from flask_login import UserMixin
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy import JSON

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

class AssessmentStage(enum.Enum):
    WAITING = "WAITING"
    GAIT = "GAIT"
    GAIT_COMPLETE = "GAIT_COMPLETE"
    RT_TEST = "RT_TEST"
    COMPLETE = "COMPLETE"

# model for a patient's assessment
class PatientAssessment(db.Model):
    __tablename__ = 'patientassessment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id')) # link to Patient
    score = db.Column(db.Integer)
    avg_reaction_time = db.Column(db.Float)
    total_rounds = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime, default=db.func.current_timestamp()) # track when test was completed
    difficulty = db.Column(db.String(20), nullable=False)
    reaction_records = db.Column(JSON) # store reaction times as a list
    memorization_time = db.Column(db.Integer)

    # Needed to access during running assessments
    is_running = db.Column(db.Boolean)
    join_code = db.Column(db.String(6), nullable=False)
    watch_connected = db.Column(db.Boolean)
    current_step = db.Column(db.Integer) # Index in STEP_ORDER

    # For time synchronization
    SYNC_CALLS = 10
    ADDITIONAL_DELAY = 6
    watch_synchroized = db.Column(db.Integer, default=False)
    browser_synchroized = db.Column(db.Integer, default=False)
    test_start = db.Column(db.DateTime, default=datetime.now())
    
    # set relationship with Patient so that we can access the associated Patient object from PatientAssessment
    patient = db.relationship('Patient', backref='assessments')

    STEP_ORDER = [
        AssessmentStage.WAITING, 
        AssessmentStage.GAIT, 
        AssessmentStage.GAIT_COMPLETE, 
        AssessmentStage.RT_TEST, 
        AssessmentStage.COMPLETE
    ]

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

    def increment_step(self):
        session = Session.object_session(self)
        self.current_step = min(self.current_step + 1, len(PatientAssessment.STEP_ORDER))
        session.commit()

    def get_current_step(self):
        return PatientAssessment.STEP_ORDER[self.current_step].value
        
    def increment_synchronization(self, device: str) -> bool:
        session = Session.object_session(self)
        if device == "watch":
            self.watch_synchroized += 1 
        if device == "browser":
            self.browser_synchroized += 1 
        session.commit()

    def can_create_test_time(self):
        return (self.browser_synchroized >= PatientAssessment.SYNC_CALLS and self.watch_synchroized >= PatientAssessment.SYNC_CALLS) \
            or self.test_start > datetime.now()

    def get_test_start(self):
        if self.test_start > datetime.now():
            timeval = (self.test_start - datetime.now())
            return round(timeval.total_seconds() * 1000 +  timeval.microseconds / 1000)
        session = Session.object_session(self)
        future_test_time = round(1000 * (PatientAssessment.ADDITIONAL_DELAY + self.memorization_time)) + random.randint(0, 5000)
        self.test_start = datetime.now() + timedelta(milliseconds=future_test_time)
        self.browser_synchroized = 0
        self.watch_synchroized = 0
        session.commit()
        timeval = (self.test_start - datetime.now())
        return round(timeval.total_seconds() * 1000 +  timeval.microseconds / 1000)


class AssessmentStageData(db.Model):
    __tablename__ = 'assessmentstagedata'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('patientassessment.id'))
    stage = db.Column(db.Enum(AssessmentStage))
    points = db.relationship('StageDataPoint', backref='stage_data', cascade="all, delete-orphan")
    
    @classmethod
    def from_json(cls, json_data: dict[str, Any], stage: AssessmentStage, assessment_id: int) -> "AssessmentStageData":
        """
        Create an AssessmentStageData instance from JSON data.
        
        Args:
            json_data (dict[str, Any]): JSON data containing assessment stage information.
            
        Returns:
            AssessmentStageData: The created AssessmentStageData instance.
        """
        stage_data = cls(
            assessment_id=assessment_id,
            stage=stage
        )
        
        for point in json_data["data"]:
            ts = datetime.fromtimestamp(point["timestamp"] / 1000.0)
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

# Models for Peak and Trough Indices and Zero Crossing Analysis

class ZeroCrossingAnalysis(db.Model):
    __tablename__ = 'zerocrossinganalysis'
    id = db.Column(db.Integer, primary_key=True)
    stage_data_id = db.Column(db.Integer, db.ForeignKey('assessmentstagedata.id'))
    peak_indices = db.relationship('PeakIndex', backref='analysis', cascade="all, delete-orphan")
    trough_indices = db.relationship('TroughIndex', backref='analysis', cascade="all, delete-orphan")
    avg_peak_distance = db.Column(db.Float)
    std_dev_peak_distance = db.Column(db.Float)
    avg_trough_distance = db.Column(db.Float)
    std_dev_trough_distance = db.Column(db.Float)

class PeakIndex(db.Model):
    __tablename__ = 'peakindex'
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('zerocrossinganalysis.id'))
    index = db.Column(db.Integer)

class TroughIndex(db.Model):
    __tablename__ = 'troughindex'
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('zerocrossinganalysis.id'))
    index = db.Column(db.Integer)

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
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
    """
    Primary user model that encompases physicians and patients
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic')) # User is always patient or physician
    
    # to be able to link Physician OR Patient profile to User
    patient_profile = db.relationship('Patient', backref='user', uselist=False)
    physician_profile = db.relationship('Physician', backref='user', uselist=False)
    
    # check if this user has a certain role
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

# model for roles
class Role(db.Model):
    """
    Add roles and a quick description
    """
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

# model for physician profile
class Physician(db.Model):
    """
    Adds Physician users. A physician is a user that manages
    Patients, can start their assessments, and views results.
    """
    __tablename__ = 'physician'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True) # every Physician corresponds to exactly one User entry
    patients = db.relationship('Patient', backref='physician', lazy=True) # one Physician can have many Patients

# model for patient profile
class Patient(db.Model):
    """
    Adds Patient users. A patient is a user that can take
    an assessment and view their results.
    """
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True) # link to User
    physician_id = db.Column(db.Integer, db.ForeignKey('physician.id')) # each Patient belongs optionallu to 1 Physician

    # Extra collected data: Not used in this project, but for PoC
    age = db.Column(db.Integer)
    height = db.Column(db.Integer)
    gender = db.Column(db.String(80))
    weight = db.Column(db.Integer)

class AssessmentStage(enum.Enum):
    """
    Denotes the various states that an assessment can be in
    """
    WAITING = "WAITING"
    GAIT = "GAIT"
    GAIT_COMPLETE = "GAIT_COMPLETE"
    RT_TEST = "RT_TEST"
    COMPLETE = "COMPLETE"

# model for a patient's assessment
class PatientAssessment(db.Model):
    """
    The object that stores a patient's assessment while it's
    running, as well as the results once it's completed.
    """

    @staticmethod
    def generate_unique_join_code() -> str:
        """
        Generates unique join code for the assessment that
        is not shared by any other running assessment.

        Returns:
            str: 6-digit code to allow the watch to join
        """
        code = f"{random.randint(0, 999999):06d}"
        while db.session.query(PatientAssessment).filter(PatientAssessment.join_code == code and PatientAssessment.is_running == True).first() is not None:
            code = f"{random.randint(0, 999999):06d}"
        return code

    __tablename__ = 'patientassessment'
    id = db.Column(db.Integer, primary_key=True)

    # Automatically set when object initialized, used to find running assessments
    is_running = db.Column(db.Boolean, default=True)
    join_code = db.Column(db.String(6), nullable=False, default=generate_unique_join_code) # Code unique to running assessments
    watch_connected = db.Column(db.Boolean) # True once watch is connected
    current_step = db.Column(db.Integer, default = 0) # Index in STEP_ORDER

    # Stored at beginning
    total_rounds = db.Column(db.Integer) # Total number of memory rounds
    num_shapes = db.Column(db.Integer) # Number of memory shapes
    date_taken = db.Column(db.DateTime, default=db.func.current_timestamp()) # Track when test was completed
    difficulty = db.Column(db.String(20), nullable=False) # Either "Easy" or "Hard"
    memorization_time = db.Column(db.Integer) # Count in seconds of amount of time for user to memorize shapes
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id')) # Link to Patient

    # Calculated at end
    score = db.Column(db.Integer) # Number of correct guesses
    memory_accuracy = db.Column(db.Float) # Float value of score / total_rounds
    avg_reaction_time = db.Column(db.Float) # ms count of reaction time
    reaction_records = db.Column(JSON) # Stores reaction times as a list

    # For time synchronization between watch and frontend
    SYNC_CALLS = 10 # Number of calls required to sync both
    ADDITIONAL_DELAY = 6 # Additional number of seconds to delay showing images as buffer
    watch_synchronized = db.Column(db.Integer, default=0) # Count of times watch has measured latency since last reset
    browser_synchronized = db.Column(db.Integer, default=0) # Count of times browser has measured latency since last reset
    test_start = db.Column(db.DateTime, default=datetime.now()) # Time at which the next memory test will occur
    
    # set relationship with Patient so that we can access the associated Patient object from PatientAssessment
    patient = db.relationship('Patient', backref='assessments')

    # Proper ordering for steps
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
        """
        Takes the current step of the assessment and increments it up
        until the final step
        """
        session = Session.object_session(self)
        self.current_step = min(self.current_step + 1, len(PatientAssessment.STEP_ORDER) - 1)
        session.commit()

    def get_current_step(self) -> str:
        """
        Returns string value of current assessment step

        Returns:
            str: String value of current step
        """
        return PatientAssessment.STEP_ORDER[self.current_step].value
        
    def increment_synchronization(self, device: str):
        """
        Increments the count of the synchronization attempts for a given device

        Args:
            device (str): String representation of either watch or browser device
        """
        session = Session.object_session(self)
        if device == "watch":
            self.watch_synchronized += 1 
        if device == "browser":
            self.browser_synchronized += 1 
        session.commit()

    def can_create_test_time(self) -> bool:
        """
        Checks whether a future time to plan RT test can be scheduled.
        Depends on browser and watch having synchronized enough times
        and there not being an existing future test start time.
        """
        return (self.browser_synchronized >= PatientAssessment.SYNC_CALLS and self.watch_synchronized >= PatientAssessment.SYNC_CALLS) \
            or self.test_start > datetime.now()

    def get_test_start(self) -> int:
        """
        Sets and gets future RT test start time

        Returns:
            int: Number of ms until next test's starting time
        """
        # If exists, simply return
        if self.test_start > datetime.now():
            timeval = (self.test_start - datetime.now())
            return round(timeval.total_seconds() * 1000)        
        
        # Create future start time
        session = Session.object_session(self)
        future_test_time = round(1000 * (PatientAssessment.ADDITIONAL_DELAY + self.memorization_time)) + random.randint(0, 5000)
        self.test_start = datetime.now() + timedelta(milliseconds=future_test_time)
        self.browser_synchronized = 0
        self.watch_synchronized = 0
        session.commit()

        # Submit time difference between now and test start
        timeval = (self.test_start - datetime.now())
        return round(timeval.total_seconds() * 1000)
        
    def run_celery_tasks(self):
        """
        Queues all celery tasks on available data.
        """
        from app.celery_tasks.tasks import memory_analysis, identify_peaks
        for stage_data in db.session.query(AssessmentStageData).filter_by(stage=AssessmentStage.GAIT, assessment_id=self.id).all():
            identify_peaks.delay(stage_data.id)
        
        for stage_data in db.session.query(AssessmentStageData).filter_by(stage=AssessmentStage.RT_TEST, assessment_id=self.id).all():
            memory_analysis.delay(stage_data.id)


class AssessmentStageData(db.Model):
    """
    For a given relevant step in the PatientAssessment (RT_TEST or GAIT),
    contains group of X, Y, Z and Timestamp data points for the test.
    """
    __tablename__ = 'assessmentstagedata'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('patientassessment.id')) # Link to PatientAssessment
    stage = db.Column(db.Enum(AssessmentStage)) # Marker for stage
    points = db.relationship('StageDataPoint', backref='stage_data', cascade="all, delete-orphan") # X, Y, Z, ts measurements
    
    @classmethod
    def from_json(cls, json_data: dict[str, Any], stage: AssessmentStage, assessment_id: int) -> "AssessmentStageData":
        """
        Create an AssessmentStageData instance from JSON data.
        
        Args:
            json_data (dict[str, Any]): JSON data containing assessment stage information.
            stage (AssessmentStage): Enum for current stage
            assessment_id (int): ID for linking PatientAssessment
            
        Returns:
            AssessmentStageData: The created AssessmentStageData instance.
        """
        stage_data = cls(
            assessment_id=assessment_id,
            stage=stage
        )

        # When GAIT, the first second should be discarded. The sensor is innacurate during that time
        initial_ts = None
        skip_first_second = stage == AssessmentStage.GAIT

        for point in json_data["data"]:
            ts = datetime.fromtimestamp(point["timestamp"] / 1000.0)

            if not initial_ts:
                initial_ts = ts
            elif skip_first_second and (ts - initial_ts).total_seconds() < 1:
                # Needed because the accelerometer spikes on startup
                continue

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
    """
    X, Y, Z and Timestamp data point from watch measurements
    """
    __tablename__ = 'stagedatapoint'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('assessmentstagedata.id')) # Link to AssessmentStageData
    timestamp = db.Column(db.DateTime(timezone=True))
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)

# Models for Peak and Trough Indices and Zero Crossing Analysis

class ZeroCrossingAnalysis(db.Model):
    """
    Celery DB object used for gait analysis from watch data
    """
    __tablename__ = 'zerocrossinganalysis'
    id = db.Column(db.Integer, primary_key=True)
    stage_data_id = db.Column(db.Integer, db.ForeignKey('assessmentstagedata.id')) # Link to AssessmentStageData
    peak_indices = db.relationship('PeakIndex', backref='analysis', cascade="all, delete-orphan") # Index of peak values
    trough_indices = db.relationship('TroughIndex', backref='analysis', cascade="all, delete-orphan") # Index of trough values
    avg_peak_distance = db.Column(db.Float) # Average distances between detected peaks in s
    std_dev_peak_distance = db.Column(db.Float) # Std dev between detected peaks in s
    avg_trough_distance = db.Column(db.Float) # Average distances between detected troughs in s
    std_dev_trough_distance = db.Column(db.Float) # Std dev between detected troughs in s

class PeakIndex(db.Model):
    __tablename__ = 'peakindex'
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('zerocrossinganalysis.id'))
    point_index  = db.Column(db.Integer)

class TroughIndex(db.Model):
    __tablename__ = 'troughindex'
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('zerocrossinganalysis.id'))
    point_index  = db.Column(db.Integer)

class MemoryAnalysis(db.Model):
    """
    Celery DB object used for memory analysis from watch data
    """
    __tablename__ = 'memoryanalysis'
    id = db.Column(db.Integer, primary_key=True)
    assessment_stage_data_id = db.Column(db.Integer, db.ForeignKey('assessmentstagedata.id'))
    time_to_move = db.Column(db.Float) # Time in ms to move hand from stand-still
    average_accl_post_threshold = db.Column(db.Float) # Average acceleration observed once user has moved in m/s2
    max_accl = db.Column(db.Float) # Maximum acceleration in m/s2

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
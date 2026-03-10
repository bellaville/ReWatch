from flask.testing import FlaskClient

from app.models import User, Patient, Physician, PatientAssessment, Role, create_profiles_for_new_users, Session
from app.db import db
from werkzeug.security import generate_password_hash
from unittest.mock import patch
from uuid import uuid4

def login(test_client, user):
    """Logs in a test user by manipulating the session."""
    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

def create_patient_user(name, email, physician: Physician | None = None):
    """Helper to create a patient user with a Patient profile.
       Optionally assigns to a physician.
    """
    patient_role = Role.query.filter_by(name="Patient").first()
    user = User(
        name=name,
        email=email,
        password=generate_password_hash("password123")
    )
    user.roles.append(patient_role)

    db.session.add(user)
    db.session.commit()

    patient = db.session.query(Patient).filter(Patient.user_id == user.id).first()

    if physician is not None:
        patient.physician_id = physician.id
        physician.patients.append(patient)
        db.session.commit()

    return user, patient

def create_physician_user(name, email):
    """Helper to create a physician user with Physician profile."""
    physician_role = Role.query.filter_by(name="Physician").first()
    user = User(
        name=name,
        email=email,
        password=generate_password_hash("password123")
    )
    user.roles.append(physician_role)
    db.session.add(user)
    db.session.commit()
    
    return user, db.session.query(Physician).filter(Physician.user_id == user.id).first()

def test_inaccessible_routes_when_not_logged_in(test_client: FlaskClient):
    """
    GIVEN A logged out user
    WHEN they attempt to visit testing endpoints
    THEN we expect it to redirect elsewhere
    """
    GET_ROUTES = [
        "/assessments/memory_test/customize",
        "/assessments/memory_test/connect",
        "/assessments/memory_test/start",
        "/assessments/memory_test/memorize",
        "/assessments/memory_test/result"
    ]

    for route in GET_ROUTES:
        response = test_client.get(route)
        assert response.status_code == 302 

def test_inaccessible_routes_when_session_not_started(test_client: FlaskClient):
    """
    GIVEN A logged-in user not current in assessment
    WHEN they attempt to visit testing endpoints
    THEN we expect it to redirect to the /customize
    """
    uuid = str(uuid4())
    user, _ = create_patient_user(uuid, f"{uuid}@example.com")
    login(test_client, user)

    GET_ROUTES = [
        "/assessments/memory_test/connect",
        "/assessments/memory_test/start",
        "/assessments/memory_test/memorize",
        "/assessments/memory_test/result"
    ]

    for route in GET_ROUTES:
        response = test_client.get(route)
        assert response.status_code == 302 
        assert response.headers['Location'].endswith("/assessments/memory_test/customize")

def test_patient_session_start(test_client: FlaskClient):
    """
    GIVEN A logged in patient user
    WHEN they attempt to create an assessment
    THEN we expect it to work successfully and begin tracking in the DB
    """
    uuid = str(uuid4())
    user, patient = create_patient_user(uuid, f"{uuid}@example.com")
    login(test_client, user)

    NUM_SHAPES = 245
    MEM_TIME = 32
    NUM_ROUNDS = 123
    DIFFICULTY = "hard"

    response = test_client.post(
        "/assessments/memory_test/customize",
        data={"num_shapes": NUM_SHAPES, "memorization_time": MEM_TIME, "num_rounds": NUM_ROUNDS, "difficulty": DIFFICULTY, "patient_id": patient.id}
    )

    assert response.status_code == 302
    assert response.headers['Location'].endswith("/assessments/memory_test/connect")

    with test_client.session_transaction() as sess:
        assert 'join_code' in sess
        assessment = db.session.query(PatientAssessment).filter(PatientAssessment.is_running == True, PatientAssessment.join_code == sess['join_code']).first()
        assert assessment is not None

    assert assessment.num_shapes == NUM_SHAPES
    assert assessment.memorization_time == MEM_TIME
    assert assessment.total_rounds == NUM_ROUNDS
    assert assessment.difficulty == DIFFICULTY
    assert assessment.patient_id == patient.id
    assert assessment.is_running
    assert assessment.current_step == 0

def test_physician_session_start(test_client: FlaskClient):
    """
    GIVEN A logged in physician user
    WHEN they attempt to create an assessment
    THEN we expect it to work successfully and begin tracking in the DB
    """
    uuid_phys = str(uuid4())
    uuid_pat = str(uuid4())
    user, physician = create_physician_user(uuid_phys, f"{uuid_phys}@example.com")
    _, patient = create_patient_user(uuid_pat, f"{uuid_pat}@example.com", physician)
    login(test_client, user)

    NUM_SHAPES = 543
    MEM_TIME = 3223
    NUM_ROUNDS = 123333
    DIFFICULTY = "hard"

    response = test_client.post(
        "/assessments/memory_test/customize",
        data={"num_shapes": NUM_SHAPES, "memorization_time": MEM_TIME, "num_rounds": NUM_ROUNDS, "difficulty": DIFFICULTY, "patient_id": patient.id}
    )

    assert response.status_code == 302
    assert response.headers['Location'].endswith("/assessments/memory_test/connect")

    with test_client.session_transaction() as sess:
        assert 'join_code' in sess
        assessment = db.session.query(PatientAssessment).filter(PatientAssessment.is_running == True, PatientAssessment.join_code == sess['join_code']).first()
        assert assessment is not None

    assert assessment.num_shapes == NUM_SHAPES
    assert assessment.memorization_time == MEM_TIME
    assert assessment.total_rounds == NUM_ROUNDS
    assert assessment.difficulty == DIFFICULTY
    assert assessment.patient_id == patient.id
    assert assessment.is_running
    assert assessment.current_step == 0

def test_physician_session_start_on_non_patient(test_client: FlaskClient):
    """
    GIVEN A logged in physician user
    WHEN they attempt to create an assessment for a patient that isn't theirs
    THEN we expect it to fail and send the user back to the customization page
    """
    uuid_phys = str(uuid4())
    uuid_pat = str(uuid4())
    user, _ = create_physician_user(uuid_phys, f"{uuid_phys}@example.com")
    _, patient = create_patient_user(uuid_pat, f"{uuid_pat}@example.com")
    login(test_client, user)

    NUM_SHAPES = 543
    MEM_TIME = 3223
    NUM_ROUNDS = 123333
    DIFFICULTY = "hard"

    response = test_client.post(
        "/assessments/memory_test/customize",
        data={"num_shapes": NUM_SHAPES, "memorization_time": MEM_TIME, "num_rounds": NUM_ROUNDS, "difficulty": DIFFICULTY, "patient_id": patient.id}
    )

    assert response.status_code == 200
    assert b"Difficulty level" in response.data
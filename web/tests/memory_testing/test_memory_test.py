import pytest
import time

from app.models import User, Patient, Physician, PatientAssessment, Role
from app.db import db
from werkzeug.security import generate_password_hash

def login(test_client, user):
    """Logs in a test user by manipulating the session."""
    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)


def create_patient_user(name, email, physician=None):
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

    patient_profile = Patient(user_id=user.id)
    if physician:
        patient_profile.physician_id = physician.id
    db.session.add(patient_profile)
    db.session.commit()

    return user, patient_profile

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

    physician_profile = Physician(user_id=user.id)
    db.session.add(physician_profile)
    db.session.commit()

    return user, physician_profile


def init_memory_test_session(sess, patient_id=None):
    """Helper to initialize session variables for memory test."""
    sess["round"] = 0
    sess["score"] = 0
    sess["reaction_times"] = []
    sess["show_test"] = False
    sess["num_shapes"] = 3
    sess["difficulty"] = "easy"
    sess["num_rounds"] = 5
    sess["memorization_time"] = 5
    if patient_id:
        sess["test_patient_id"] = patient_id


def test_start_memory_test_initializes_session(test_client):
    """GIVEN logged-in user
       WHEN start_memory_test is accessed
       THEN session variables should initialize properly
    """
    user, patient = create_patient_user("TestUser", "test@example.com")
    login(test_client, user)

    response = test_client.get("/assessments/memory_test/start")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert sess["round"] == 0
        assert sess["score"] == 0
        assert sess["reaction_times"] == []
        assert sess["show_test"] is False
        assert sess["test_patient_id"] == patient.id


def test_memory_memorize_generates_shapes(test_client):
    """GIVEN logged-in user with initialized session for memory test
       WHEN the memorize phase is accessed
       THEN session variables for current set, positions, colours, and memorization time are set correctly
    """
    user, patient = create_patient_user("TestUser2", "test2@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)

    response = test_client.get("/assessments/memory_test/memorize")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert "current_set" in sess
        assert len(sess["current_set"]) == 3
        assert "shape_positions" in sess
        assert "shape_colours" in sess
        assert "memorization_time" in sess


def test_memory_test_post_scoring(test_client):
    """GIVEN logged-in user with a current memory test round
       WHEN the user posts a response in the comparison phase
       THEN reaction time is recorded, score is updated, and round is incremented
    """
    user, patient = create_patient_user("TestUser3", "test3@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["previous_set"] = ["circle", "square"]
        sess["current_set"] = ["circle", "square"]   # Same
        sess["reaction_times"] = []
        sess["start_time"] = time.time() - 0.5  # simulate reaction time

    response = test_client.post(
        "/assessments/memory_test/response",
        data={"choice": "Same"}
    )

    assert response.status_code == 302  # redirect to next memorize phase

    with test_client.session_transaction() as sess:
        assert len(sess["reaction_times"]) == 1
        assert sess["score"] == 1   # Correct answer
        assert sess["round"] == 1


def test_memory_test_get_generates_comparison_set(test_client):
    """GIVEN logged-in user with a previous memory test round
       WHEN the comparison phase is accessed via GET
       THEN session variables for the current set, positions, colours, and start_time are correctly initialized
    """
    user = User(name="TestUser4", email="test4@example.com", password="pass")
    db.session.add(user)
    db.session.commit()
    login(test_client, user)

    with test_client.session_transaction() as sess:
        sess["round"] = 0
        sess["previous_set"] = ["triangle"]
        sess["num_shapes"] = 1
        sess["difficulty"] = "easy"

    response = test_client.get("/assessments/memory_test/response")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert "current_set" in sess
        assert "shape_positions" in sess
        assert "shape_colours" in sess
        assert "start_time" in sess


def test_saving_patient_assessment(test_client):
    """GIVEN a patient user
       WHEN they complete a memory test
       THEN a new PatientAssessment is saved in the database with correct values
    """
    user, patient_profile = create_patient_user("Test Patient", "patient1@example.com")
    login(test_client, user)

    # Simulate test session
    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient_profile.id)
        sess["score"] = 3
        sess["reaction_times"] = [0.5, 0.6, 0.4]

    # Call the result route to save assessment
    response = test_client.get("/assessments/memory_test/result")
    assert response.status_code == 200

    # Verify database
    assessment = PatientAssessment.query.filter_by(patient_id=patient_profile.id).first()
    assert assessment is not None
    assert assessment.score == 3
    assert assessment.total_rounds == 5
    expected_avg = sum([0.5, 0.6, 0.4]) / 3
    assert pytest.approx(assessment.avg_reaction_time, 0.01) == expected_avg

def test_physician_can_save_assessment_for_patient(test_client):
    """GIVEN a physician and a patient assigned to them
       WHEN physician initiates memory test for patient
       THEN the PatientAssessment is correctly linked to the patient
    """
    physician_user, physician_profile = create_physician_user("Dr. Strange", "drstrange@example.com")
    patient_user, patient_profile = create_patient_user("Peter Parker", "peter@example.com", physician=physician_profile)
    login(test_client, physician_user)

    # Simulate physician session selecting patient
    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(physician_user.id)
        init_memory_test_session(sess, patient_id=patient_profile.id)
        sess["score"] = 4
        sess["reaction_times"] = [0.5, 0.7, 0.6, 0.8]

    # Call result route
    response = test_client.get("/assessments/memory_test/result")
    assert response.status_code == 200

    assessment = PatientAssessment.query.filter_by(patient_id=patient_profile.id).first()
    assert assessment is not None
    assert assessment.score == 4
    assert assessment.total_rounds == 5

import pytest
import time

from app.models import User, Patient, Physician, PatientAssessment, Role
from app.db import db
from werkzeug.security import generate_password_hash
from unittest.mock import patch

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
       THEN session variables for current shapes, positions, colours, and memorization time are set correctly
    """
    user, patient = create_patient_user("TestUser2", "test2@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)

    response = test_client.get("/assessments/memory_test/memorize")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert "current_shapes" in sess
        assert len(sess["current_shapes"]) == 3
        assert "shape_positions" in sess
        assert "current_colours" in sess
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
        sess["previous_shapes"] = ["circle", "square"]
        sess["current_shapes"] = ["circle", "square"]   # Same
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
       THEN session variables for the current shapes, positions, colours, and start_time are correctly initialized
    """
    user = User(name="TestUser4", email="test4@example.com", password="pass")
    db.session.add(user)
    db.session.commit()
    login(test_client, user)

    with test_client.session_transaction() as sess:
        sess["round"] = 0
        sess["previous_shapes"] = ["triangle"]
        sess["previous_colours"] = ["green"]
        sess["num_shapes"] = 1
        sess["difficulty"] = "easy"

    response = test_client.get("/assessments/memory_test/response")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert "current_shapes" in sess
        assert "shape_positions" in sess
        assert "current_colours" in sess
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

def test_memory_test_hard_mode_correct_match(test_client):
    """GIVEN a patient in hard difficulty mode
       WHEN they respond with the same shapes and colours
       THEN they should get a point
    """
    user, patient = create_patient_user("HardTest1", "hard1@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "hard"
        sess["previous_shapes"] = ["circle", "square"]
        sess["previous_colours"] = ["blue", "red"]
        sess["current_shapes"] = ["circle", "square"]
        sess["current_colours"] = ["blue", "red"]
        sess["start_time"] = time.time() - 0.3

    response = test_client.post(
        "/assessments/memory_test/response",
        data={"choice": "Same"}
    )

    assert response.status_code == 302  # redirect
    with test_client.session_transaction() as sess:
        assert sess["score"] == 1
        assert sess["round"] == 1


def test_memory_test_hard_mode_wrong_colour(test_client):
    """GIVEN a patient in hard mode
       WHEN shapes match but colours differ
       THEN score should NOT increase
    """
    user, patient = create_patient_user("HardTest2", "hard2@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "hard"
        sess["previous_shapes"] = ["circle", "square"]
        sess["previous_colours"] = ["blue", "red"]
        sess["current_shapes"] = ["circle", "square"]
        sess["current_colours"] = ["green", "red"]  # one colour differs
        sess["start_time"] = time.time() - 0.4

    response = test_client.post(
        "/assessments/memory_test/response",
        data={"choice": "Same"}
    )

    assert response.status_code == 302
    with test_client.session_transaction() as sess:
        assert sess["score"] == 0
        assert sess["round"] == 1


def test_memory_test_hard_mode_wrong_shape(test_client):
    """GIVEN a patient in hard mode
       WHEN a shape differs (even if colours match)
       THEN score should NOT increase
    """
    user, patient = create_patient_user("HardTest3", "hard3@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "hard"
        sess["previous_shapes"] = ["circle", "square"]
        sess["previous_colours"] = ["blue", "red"]
        sess["current_shapes"] = ["circle", "triangle"]  # shape differs
        sess["current_colours"] = ["blue", "red"]
        sess["start_time"] = time.time() - 0.2

    response = test_client.post(
        "/assessments/memory_test/response",
        data={"choice": "Same"}
    )

    assert response.status_code == 302
    with test_client.session_transaction() as sess:
        assert sess["score"] == 0
        assert sess["round"] == 1


def test_memory_test_hard_mode_different_choice_correct(test_client):
    """GIVEN a patient in hard mode
       WHEN the user chooses 'Different' and shapes+colours differ
       THEN score should increase
    """
    user, patient = create_patient_user("HardTest4", "hard4@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "hard"
        sess["previous_shapes"] = ["circle", "square"]
        sess["previous_colours"] = ["blue", "red"]
        sess["current_shapes"] = ["triangle", "star"]
        sess["current_colours"] = ["green", "yellow"]
        sess["start_time"] = time.time() - 0.1

    response = test_client.post(
        "/assessments/memory_test/response",
        data={"choice": "Different"}
    )

    assert response.status_code == 302
    with test_client.session_transaction() as sess:
        assert sess["score"] == 1
        assert sess["round"] == 1


def test_memory_test_full_run_easy_mode(test_client):
    """
    GIVEN a patient in easy mode with pre-determined shapes
    WHEN the user completes all rounds choosing 'Same' with identical shape sets
    THEN the score, round count, and reaction times should increment correctly
    """
    user, patient = create_patient_user("EasyFullRun", "easyfullrun@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "easy"
        sess["num_rounds"] = 2

    # setting shapes to always be identifical between rounds
    with patch("app.memory_test.random.sample") as mock_sample:
        mock_sample.return_value = ["circle", "square", "triangle"]

        for _ in range(2):
            # memorize phase
            response = test_client.get("/assessments/memory_test/memorize")
            assert response.status_code == 200

            # comparison GET
            response = test_client.get("/assessments/memory_test/response")
            assert response.status_code == 200

            # submitn correct answer
            response = test_client.post("/assessments/memory_test/response", data={"choice": "Same"})
            assert response.status_code == 302 # "found", redirects user to another page

    with test_client.session_transaction() as sess:
        assert sess["round"] == 2
        assert sess["score"] == 2
        assert len(sess["reaction_times"]) == 2
        

def test_memory_test_full_run_hard_mode(test_client):
    """
    GIVEN a patient in hard with pre-determined shapes and colours
    WHEN the user completes all rounds choosing 'Same' with identical shape-colour sets
    THEN the score, round count, and reaction times should increment correctly
    """
    user, patient = create_patient_user("HardFullRun", "hardfull@example.com")
    login(test_client, user)

    with test_client.session_transaction() as sess:
        init_memory_test_session(sess, patient_id=patient.id)
        sess["difficulty"] = "hard"
        sess["num_rounds"] = 2

    # pre-assign shapes and colours using patch
    # random.random: force < 0.5 to always reuse memorized set
    with patch("app.memory_test.random.random", return_value=0.0), \
        patch("app.memory_test.random.sample") as mock_sample, \
        patch("app.memory_test.random.choice") as mock_choice:
        mock_sample.return_value = ["circle", "square", "triangle"]
        mock_choice.return_value = "red" # just make all shapes red to keep it simple
        # since we already covered testing for colour correctness in previous test cases

        for _ in range(2):
            response = test_client.get("/assessments/memory_test/memorize")
            assert response.status_code == 200

            response = test_client.get("/assessments/memory_test/response")
            assert response.status_code == 200

            response = test_client.post("/assessments/memory_test/response", data={"choice": "Same"})
            assert response.status_code == 302
        
    with test_client.session_transaction() as sess:
        assert sess["round"] == 2
        assert sess["score"] == 2
        assert len(sess["reaction_times"]) == 2

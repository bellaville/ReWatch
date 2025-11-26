import pytest
import time
from flask import session
from app.models import User
from app import db

def login(test_client, user):
    """Logs in a test user by manipulating the session."""
    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

def test_start_memory_test_initializes_session(test_client):
    """GIVEN logged-in user
       WHEN start_memory_test is accessed
       THEN session variables should initialize properly
    """
    user = User(name="TestUser", email="test@example.com", password="pass")
    db.session.add(user)
    db.session.commit()
    login(test_client, user)

    response = test_client.get("/assessments/memory_test/start")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert sess["round"] == 0
        assert sess["score"] == 0
        assert sess["reaction_times"] == []
        assert sess["show_test"] is False


def test_memory_memorize_generates_shapes(test_client):
    """Ensure memorize phase generates shapes, positions, colours."""
    user = User(name="TestUser2", email="test2@example.com", password="pass")
    db.session.add(user)
    db.session.commit()
    login(test_client, user)

    # Initialize session values
    with test_client.session_transaction() as sess:
        sess["round"] = 0
        sess["num_shapes"] = 3
        sess["difficulty"] = "easy"
        sess["num_rounds"] = 5

    response = test_client.get("/assessments/memory_test/memorize")
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        assert "current_set" in sess
        assert len(sess["current_set"]) == 3
        assert "shape_positions" in sess
        assert "shape_colours" in sess
        assert "memorization_time" in sess


def test_memory_test_post_scoring(test_client):
    """Test that POSTing the user's choice correctly records reaction time and increments round."""
    user = User(name="TestUser3", email="test3@example.com", password="pass")
    db.session.add(user)
    db.session.commit()
    login(test_client, user)

    with test_client.session_transaction() as sess:
        sess["round"] = 0
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


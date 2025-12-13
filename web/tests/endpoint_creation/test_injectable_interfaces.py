from flask import Blueprint

from app.models import User
from app.utilities.injection_routing import injection_route

injection_test = Blueprint('injection_testing', __name__)


@injection_route(injection_test, '/test/<user_id>', methods=["POST"])
def save_acceleration_test_data(user: User):
    """
    Save acceleration test data sent from watch client as JSON file.
    """
    assert user
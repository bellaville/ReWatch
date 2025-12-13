from flask import Blueprint, jsonify

from app.models import User
from app.utilities.injection_routing import injection_route

injection_test = Blueprint('injection_testing', __name__)

@injection_route(injection_test, '/test/<user_id>', methods=["POST"])
def user_injection_url(user: User):
    """
    Capture user ID, inject user information into the URL, and respond with it
    """
    return jsonify({"userid": user.id, "email": user.email}), 200
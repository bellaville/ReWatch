from flask import Blueprint, jsonify

from app.models import User, PatientAssessment
from app.utilities.injection_routing import injection_route

injection_test = Blueprint('injection_testing', __name__)

@injection_route(injection_test, '/test/<user_id>', methods=["POST"])
def user_injection_url(user: User):
    """
    Capture user ID, inject user information into the function, and respond with it
    """
    return jsonify({"userid": user.id, "email": user.email}), 200

@injection_route(injection_test, '/test/<assessment_id>/<user_id>', methods=["POST"])
def user_and_assessment_injection_url(user: User, assessment: PatientAssessment):
    """
    Capture user ID and assessment ID, inject user and assessment information into the 
    function, and respond with it
    """
    return jsonify({"userid": user.id, "email": user.email, "assessment_id": assessment.id}), 200
from flask import Blueprint, request, jsonify

from app.db import db
from app.models import AssessmentStageData

accel_test = Blueprint('accel_test', __name__)

@accel_test.route('/test/debug/accel', methods=["POST"])
def save_acceleration_test_data():
    """
    Save acceleration test data sent from watch client as 
    AssessmentStageData entries in the database.
    """
    assessment_data = AssessmentStageData.from_json(request.get_json())
    db.session.add(assessment_data)
    db.session.commit()
    
    return jsonify({"status": "success"}), 200

@accel_test.route('/test/debug/accel', methods=["GET"])
def get_acceleration_test_data():
    """
    Provide all acceleration test data stored in the database.
    """
    assessment_data = db.session.query(AssessmentStageData).all()
    
    return jsonify([data.to_json() for data in assessment_data])
    
    
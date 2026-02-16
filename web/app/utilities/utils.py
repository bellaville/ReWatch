from flask import session

from app.models import PatientAssessment, Patient

def get_patient_assessment_data(patient_id):
    """
    Fetch assessments and prepare chart data for a patient
    """
    results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.asc()).all()

    # Create the dataset from the memory test for charts
    chart_scores = []
    chart_avg_reactions = []
    correct_reactions = []
    incorrect_reactions = []

    for assessment in results:
        date_label = assessment.date_taken.strftime("%Y-%m-%d")
        # average reactoin time (one per assessment)
        chart_avg_reactions.append({
            "x": date_label,
            "y": assessment.avg_reaction_time,
            "difficulty": assessment.difficulty
        })
        chart_scores.append({
            "x": date_label,
            "y": assessment.score,
            "difficulty": assessment.difficulty
        })

        # Individual reaction times (many per assessment)
        for rt in assessment.reaction_records:
            point = {
                "x": date_label,
                "y": rt["time"],
                "difficulty": assessment.difficulty,
                "num_shapes": rt["num_shapes"],
            }

            if rt["correct"]:
                correct_reactions.append(point)
            else:
                incorrect_reactions.append(point)

    return results, chart_scores, chart_avg_reactions, correct_reactions, incorrect_reactions

def get_patient_information(patient_id):
    patient_age = Patient.query.filter_by(id=patient_id).first().age
    patient_height = Patient.query.filter_by(id=patient_id).first().height
    patient_gender = Patient.query.filter_by(id=patient_id).first().gender
    patient_weight = Patient.query.filter_by(id=patient_id).first().weight

    return patient_age, patient_height, patient_gender, patient_weight

def get_real_watch_status(user_id):
    """Check actual status from DB/API. Replace session fallback later."""
    status = session.get('watch_connected', False)
    # TODO: Query DB or Samsung Health/Watch API
    return status

def connect_watch(user_id):
    """Attempt connection to galaxy watch. Returns True on success."""
    try:
        # TODO: Integrate Galaxy Watch 7 SDK/API
        print(f"Connecting watch for user {user_id}")
        return True  # Simulate success
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def disconnect_watch(user_id):
    """Disconnect watch."""
    try:
        # TODO: Unpair/disconnect via API
        print(f"Disconnecting watch for user {user_id}")
        return True
    except Exception:
        return False

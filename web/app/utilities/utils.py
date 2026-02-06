from flask import session

from app.models import PatientAssessment, Patient

def get_patient_assessment_data(patient_id):
    """
    Fetch assessments and prepare chart data for a patient
    """
    results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.desc()).all()

    # Reverse once so charts go from oldest to newest
    results = list(reversed(results))    
    
    # Create the dataset from the memory test for charts
    chart_labels = [r.date_taken.strftime("%Y-%m-%d") for r in results]
    chart_scores = [r.score for r in results]
    chart_reaction_times = [r.avg_reaction_time for r in results]

    return results, chart_labels, chart_scores, chart_reaction_times

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

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
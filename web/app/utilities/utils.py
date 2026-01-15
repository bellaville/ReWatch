from app.models import PatientAssessment

def get_patient_assessment_data(patient_id):
    """
    Fetch assessments and prepare chart data for a patient
    """
    results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.asc()).all()

    # Reverse once so charts go from oldest to newest
    #results = list(reversed(results))    
    
    # Create the dataset from the memory test for charts
    chart_labels = [r.date_taken.strftime("%Y-%m-%d") for r in results]
    chart_scores = [r.score for r in results]
    chart_avg_reactions = [r.avg_reaction_time for r in results]
    all_reaction_times = [r.reaction_times for r in results]

    return results, chart_labels, chart_scores, chart_avg_reactions, all_reaction_times
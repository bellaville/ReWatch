from app.models import PatientAssessment

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
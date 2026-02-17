from app.models import PatientAssessment, Patient
import statistics

def get_patient_assessment_data(patient_id):
    """
    Fetch assessments and prepare chart data for a patient
    """
    results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.asc()).all()

    # Create the dataset from the memory test for charts
    chart_scores = []
    correct_reactions = []
    incorrect_reactions = []

    chart_avg_reactions = []
    chart_reaction_std = []
    chart_correct_avg = []
    chart_correct_std = []
    chart_incorrect_avg = []
    chart_incorrect_std = []

    for assessment in results:
        date_label = assessment.date_taken.strftime("%Y-%m-%d")

        # collect all reaction times for this assessment
        reaction_times = [rt["time"] for rt in assessment.reaction_records]
        correct_times = [rt["time"] for rt in assessment.reaction_records if rt["correct"]]
        incorrect_times = [rt["time"] for rt in assessment.reaction_records if not rt["correct"]]

        # ORIGINAL STD DEV
        if len(reaction_times) > 1:
            std_dev = statistics.stdev(reaction_times)
        else:
            std_dev = 0

        # std dev per assessment
        chart_reaction_std.append({
            "x": date_label,
            "y": std_dev,
            "difficulty": assessment.difficulty
        })

        # CORRECT AVG + STD DEV
        if len(correct_times) > 0:
            avg_correct = sum(correct_times) / len(correct_times)
        else:
            avg_correct = 0

        if len(correct_times) > 1:
            correct_std = statistics.stdev(correct_times)
        else:
            correct_std = 0

        # average + std dev per assessment (correct only)
        chart_correct_avg.append({
            "x": date_label,
            "y": avg_correct,
            "difficulty": assessment.difficulty
        })

        chart_correct_std.append({
            "x": date_label,
            "y": correct_std,
            "difficulty": assessment.difficulty
        })

        # INCORRECT AVG + STD DEV
        if len(incorrect_times) > 0:
            avg_incorrect = sum(incorrect_times) / len(incorrect_times)
        else:
            avg_incorrect = 0

        if len(incorrect_times) > 1:
            incorrect_std = statistics.stdev(incorrect_times)
        else:
            incorrect_std = 0

        # average + std dev per assessment (incorrect only)
        chart_incorrect_avg.append({
            "x": date_label,
            "y": avg_incorrect,
            "difficulty": assessment.difficulty
        })

        chart_incorrect_std.append({
            "x": date_label,
            "y": incorrect_std,
            "difficulty": assessment.difficulty
        })

        # average reaction time (one per assessment)
        chart_avg_reactions.append({
            "x": date_label,
            "y": assessment.avg_reaction_time,
            "difficulty": assessment.difficulty
        })

        chart_scores.append({
            "x": date_label,
            "y": (assessment.score/assessment.total_rounds)*100,
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

    return results, chart_scores, chart_avg_reactions, correct_reactions, incorrect_reactions, chart_reaction_std, chart_correct_avg, chart_correct_std, chart_incorrect_avg, chart_incorrect_std

def get_patient_information(patient_id):
    patient_age = Patient.query.filter_by(id=patient_id).first().age
    patient_height = Patient.query.filter_by(id=patient_id).first().height
    patient_gender = Patient.query.filter_by(id=patient_id).first().gender
    patient_weight = Patient.query.filter_by(id=patient_id).first().weight

    return patient_age, patient_height, patient_gender, patient_weight
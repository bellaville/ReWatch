from app.models import PatientAssessment, Patient, ZeroCrossingAnalysis, AssessmentStageData, AssessmentStage
import statistics


def avg_and_std(values):
    """
    Calculate the average and standard deviation of given reaction times
    """
    if not values:
        return 0, 0

    avg = sum(values) / len(values)
    if len(values) > 1:
        std = statistics.stdev(values)
    else:
        std = 0.0
    return avg, std


def build_point(date_label, value, difficulty):
    """
    Build a chart data point with date (x), value (y), and difficulty
    """
    return {
        "x": date_label,
        "y": value,
        "difficulty": difficulty
    }


def get_patient_assessment_data(patient_id):
    """
    Fetch assessments and prepare chart data for a patient
    """
    results = PatientAssessment.query.filter_by(patient_id=patient_id) \
        .order_by(PatientAssessment.date_taken.asc()).all()

    # Create the dataset from the memory test for charts in dictionary format
    chart_data = {
        "scores": [],
        "reactions": {
            "average": [],
            "std": [],
            "correct_avg": [],
            "correct_std": [],
            "incorrect_avg": [],
            "incorrect_std": [],
            "correct_points": [],
            "incorrect_points": []
        }
    }

    for assessment in results:
        date_label = assessment.date_taken.strftime("%Y-%m-%d")
        difficulty = assessment.difficulty

        # collect all reaction times for this assessment
        reaction_times = [rt["time"] for rt in assessment.reaction_records]
        correct_times = [rt["time"] for rt in assessment.reaction_records if rt["correct"]]
        incorrect_times = [rt["time"] for rt in assessment.reaction_records if not rt["correct"]]

        # all reactions
        all_avg, all_std = avg_and_std(reaction_times)
        chart_data["reactions"]["average"].append(build_point(date_label, all_avg, difficulty))
        chart_data["reactions"]["std"].append(build_point(date_label, all_std, difficulty))

        # correct reactions
        correct_avg, correct_std = avg_and_std(correct_times)
        chart_data["reactions"]["correct_avg"].append(build_point(date_label, correct_avg, difficulty))
        chart_data["reactions"]["correct_std"].append(build_point(date_label, correct_std, difficulty))

        # incorrect reactions
        incorrect_avg, incorrect_std = avg_and_std(incorrect_times)
        chart_data["reactions"]["incorrect_avg"].append(build_point(date_label, incorrect_avg, difficulty))
        chart_data["reactions"]["incorrect_std"].append(build_point(date_label, incorrect_std, difficulty))

        # memory score
        score_percent = (assessment.score / assessment.total_rounds) * 100
        chart_data["scores"].append(build_point(date_label, score_percent, difficulty))

        # Individual reaction times (many per assessment)
        for rt in assessment.reaction_records:
            point = {
                "x": date_label,
                "y": rt["time"],
                "difficulty": assessment.difficulty,
                "num_shapes": rt["num_shapes"],
            }

            if rt["correct"]:
                chart_data["reactions"]["correct_points"].append(point)
            else:
                chart_data["reactions"]["incorrect_points"].append(point)

    return results, chart_data


def get_patient_information(patient_id):
    """
    Fetch all corresponding profile information of a selected patient
    """
    patient_age = Patient.query.filter_by(id=patient_id).first().age
    patient_height = Patient.query.filter_by(id=patient_id).first().height
    patient_gender = Patient.query.filter_by(id=patient_id).first().gender
    patient_weight = Patient.query.filter_by(id=patient_id).first().weight

    return patient_age, patient_height, patient_gender, patient_weight


def get_gait_zero_crossing(patient_assessment_id):
    """
    Fetch zero-crossing gait analysis metrics for a specific assessment
    """
    gait_analysis = ZeroCrossingAnalysis.query. \
        join(AssessmentStageData, ZeroCrossingAnalysis.stage_data_id == AssessmentStageData.id). \
        join(PatientAssessment, AssessmentStageData.assessment_id == PatientAssessment.id). \
        filter(
        PatientAssessment.id == patient_assessment_id,
        AssessmentStageData.stage == AssessmentStage.GAIT
    ).first()

    if gait_analysis:
        return {
            'avg_peak_distance': gait_analysis.avg_peak_distance,
            'std_dev_peak_distance': gait_analysis.std_dev_peak_distance,
            'avg_trough_distance': gait_analysis.avg_trough_distance,
            'std_dev_trough_distance': gait_analysis.std_dev_trough_distance,
            'num_peaks': len(gait_analysis.peak_indices),
            'num_troughs': len(gait_analysis.trough_indices)
        }
    return None

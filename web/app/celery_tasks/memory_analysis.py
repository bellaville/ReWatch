import pandas as pd
import numpy as np

from celery_app import celery
from app.models import AssessmentStageData, MemoryAnalysis
from app import db

@celery.task(name="memory_analysis")
def memory_analysis(assessment_stage_data_id: int):
    """
    Perform memory analysis on the given AssessmentStageData.

    Args:
        assessment_stage_data_id (int): ID of the AssessmentStageData to analyze.

    Raises:
        ValueError: If the AssessmentStageData is not found or if analysis cannot be performed.
    """

    # Retrieve AssessmentStageData from database
    data = db.session.get(AssessmentStageData, assessment_stage_data_id)

    if not data:
        raise ValueError(f"AssessmentStageData with ID {assessment_stage_data_id} not found.")

    # Convert AssessmentStageData to DataFrame
    table = pd.DataFrame(
        [
            {"X": point.x, "Y": point.y, "Z": point.z, "Timestamp": point.timestamp}
            for point in data.points
        ]
    )

    table = table.sort_values(by="Timestamp").reset_index(drop=True)

    # Set parameters
    threshold = 0.2

    # 1. Take Euclidian norm of each row
    table['norm'] = np.linalg.norm(table[['X','Y','Z']].values, axis=1)

    # 2. Get maximum norm value
    max_norm = table['norm'].max()

    if max_norm < threshold:
        raise ValueError("Maximum norm value is below threshold; cannot perform analysis.")

    # 3. Identify first > threshold time point in one liner
    above_threshold = table.loc[table['norm'] > threshold, 'Timestamp']
    first_above_threshold = above_threshold.min()

    # 4. Calculate time taken to reach threshold
    time_taken = first_above_threshold - table['Timestamp'].min()

    # 5. For all points >= first_above_threshold, calculate average norm
    relevant_points = table[table['Timestamp'] >= first_above_threshold]
    average_norm = relevant_points['norm'].mean()

    # Store results in database
    analysis = MemoryAnalysis(
        assessment_stage_data_id=assessment_stage_data_id,
        time_to_move=time_taken.total_seconds() * 1000,
        average_accl_post_threshold=average_norm,
        max_accl=max_norm
    )

    db.session.add(analysis)
    db.session.commit()
from flask.testing import FlaskClient
import numpy as np
import pytest
from scipy.interpolate import CubicSpline
from datetime import datetime, timedelta

from app.models import StageDataPoint, AssessmentStageData, AssessmentStage, MemoryAnalysis
from app import db
from app.celery_tasks.memory_analysis import memory_analysis

@pytest.fixture
def generate_stage_data_points():
    """
    Generate StageDataPoint entries from the hand-estimated sketch data
    using a cubic spline and an arbitrary but fixed direction.
    """
    assessment = AssessmentStageData(
        stage=AssessmentStage.REACTION
    )

    db.session.add(assessment)
    db.session.commit()

    # Creating accleleration data based on hand-estimated sketch
    t_points = np.array([0, 20, 40, 60, 80, 95, 110, 125, 150, 175, 200], dtype=float)
    a_points = np.array([0.02, 0.03, 0.15, 0.55, 0.85, 0.92, 0.90, 0.75, 0.45, 0.25, 0.15], dtype=float)

    spline = CubicSpline(t_points, a_points, bc_type="natural")

    # Sampling parameters
    dt_ms = 10  # 10 ms intervals
    direction=(0.3, 0.4, 0.866)
    t_samples = np.arange(t_points.min(), t_points.max() + dt_ms, dt_ms)

    # Evaluate spline at sample points
    accel_norm = np.abs(spline(t_samples))

    # Normalize direction
    direction = np.asarray(direction, dtype=float)
    direction = direction / np.linalg.norm(direction)

    # Compute x, y, z components
    x_vals = accel_norm * direction[0]
    y_vals = accel_norm * direction[1]
    z_vals = accel_norm * direction[2]

    # Add StageDataPoints to the assessment
    points = []
    start_time = datetime.now()
    for t_ms, x, y, z in zip(t_samples, x_vals, y_vals, z_vals):
        points.append(
            StageDataPoint(
                sensor_id=assessment.id,
                timestamp=start_time + timedelta(milliseconds=float(t_ms)),
                x=float(x),
                y=float(y),
                z=float(z)
            )
        )

    assessment.points = points

    db.session.add(assessment)
    db.session.commit()

    return assessment.id

def test_memory_analysis(test_client: FlaskClient, generate_stage_data_points: int):
    """
    GIVEN an AssessmentStageData with generated StageDataPoints
    WHEN the memory_analysis task is executed
    THEN the MemoryAnalysis results are correctly computed and stored in the database.
    """
    assessment_stage_data_id = generate_stage_data_points

    # Run the memory analysis task
    memory_analysis(assessment_stage_data_id)

    # Retrieve the MemoryAnalysis from the database
    analysis: MemoryAnalysis = MemoryAnalysis.query.filter_by(
        assessment_stage_data_id=assessment_stage_data_id
    ).first()

    assert analysis is not None, "MemoryAnalysis should be created."

    # Validate computed values (these expected values are based on the generated data)
    assert analysis.time_to_move <= 60 and analysis.time_to_move >= 40, "Time to move should be between 40 and 60 ms."
    assert analysis.average_accl_post_threshold > 0, "Average acceleration post-threshold should be positive."
    assert analysis.max_accl > 0.9 and analysis.max_accl < 1.0, "Max acceleration should be between 0.9 and 1.0 G."

def test_invalid_assessment_id(test_client: FlaskClient):
    """
    GIVEN an invalid AssessmentStageData ID
    WHEN the memory_analysis task is executed
    THEN a ValueError is raised.
    """
    non_existent_id = (db.session.query(db.func.max(AssessmentStageData.id)).scalar() or 0) + 1

    with pytest.raises(ValueError) as excinfo:
        memory_analysis(non_existent_id)

    assert f"AssessmentStageData with ID {non_existent_id} not found." in str(excinfo.value)

def test_memory_analysis_celery_integration(test_client: FlaskClient, generate_stage_data_points: int):
    """
    GIVEN an AssessmentStageData with generated StageDataPoints
    WHEN the memory_analysis task is executed
    THEN the MemoryAnalysis results are correctly computed and stored in the database.
    """
    assessment_stage_data_id = generate_stage_data_points

    identifier = memory_analysis.delay(assessment_stage_data_id)

    # Wait for the task to complete
    result = identifier.get(timeout=10)

    assert result is None, "The Celery task should return None."

    # Retrieve the MemoryAnalysis from the database
    analysis: MemoryAnalysis = MemoryAnalysis.query.filter_by(
        assessment_stage_data_id=assessment_stage_data_id
    ).first()

    assert analysis is not None, "MemoryAnalysis should be created."

    # Validate computed values (these expected values are based on the generated data)
    assert analysis.time_to_move <= 60 and analysis.time_to_move >= 40, "Time to move should be between 40 and 60 ms."
    assert analysis.average_accl_post_threshold > 0, "Average acceleration post-threshold should be positive."
    assert analysis.max_accl > 0.9 and analysis.max_accl < 1.0, "Max acceleration should be between 0.9 and 1.0 G."

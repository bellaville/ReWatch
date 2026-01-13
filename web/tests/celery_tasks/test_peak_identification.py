from flask.testing import FlaskClient
import pytest
from datetime import datetime, timedelta
import numpy as np

from app import db
from app.models import AssessmentStageData, AssessmentStage, StageDataPoint, ZeroCrossingAnalysis
from app.celery_tasks.peak_identification import identify_peaks

def create_sinusoidal_data(stage_data: AssessmentStageData, amplitude: float, frequency: float, duration: float, fs: int):
    """
    Helper function to create sinusoidal data points and add them to the given AssessmentStageData.
    
    Args:
        stage_data (AssessmentStageData): The assessment stage data to which points will be added.
        amplitude (float): Maximum amplitude of the sinusoidal wave.
        frequency (float): Frequency of the sinusoidal wave in Hz.
        duration (float): Duration for which to generate data in seconds.
        fs (int): Sampling frequency in Hz.
    """
    t = np.arange(0, duration, 1/fs)  # Time vector
    base_time = datetime.now()

    for ti in t:
        x = amplitude * np.sin(2 * np.pi * frequency * ti)
        y = amplitude * np.sin(2 * np.pi * frequency * ti)
        z = amplitude * np.sin(2 * np.pi * frequency * ti)
        
        point = StageDataPoint(
            timestamp=base_time + timedelta(milliseconds=int(ti*1000)),
            x=x,
            y=y,
            z=z
        )
        stage_data.points.append(point)

@pytest.fixture
def sample_assessment_stage_data(test_client: FlaskClient) -> AssessmentStageData:
    """
    Create a sample AssessmentStageData with sinusoidal data for testing.

    Args:
        test_client (FlaskClient): The Flask test client fixture.

    Returns:
        AssessmentStageData: The created assessment stage data with points.
    """
    stage_data = AssessmentStageData(
        stage=AssessmentStage.GAIT
    )
    
    # Add 5 periods of sinusoidal data at 100 Hz and period of 2 seconds
    fs = 100  # Sampling frequency
    total_time = 10  # Total time in seconds

    create_sinusoidal_data(stage_data, 1.0, 0.5, total_time, fs)

    db.session.add(stage_data)
    db.session.commit()
    
    return stage_data

def test_identify_peaks(test_client: FlaskClient, sample_assessment_stage_data: AssessmentStageData):
    """
    GIVEN a sample AssessmentStageData with sinusoidal data
    WHEN the identify_peaks function is called
    THEN peaks and troughs are correctly identified and stored in the database.
    """
    # Run the peak identification task
    identify_peaks(sample_assessment_stage_data.id)
    
    # Retrieve the updated ZeroCrossingAnalysis from the database
    analysis: ZeroCrossingAnalysis = ZeroCrossingAnalysis.query.filter_by(
        stage_data_id=sample_assessment_stage_data.id
    ).first()
    
    assert analysis is not None, "ZeroCrossingAnalysis should be created."
    assert len(analysis.peak_indices) > 0, "There should be detected peak indices."
    assert len(analysis.trough_indices) > 0, "There should be detected trough indices."
    
    # Check that average distances are 2 seconds apart (since period is 2s, peaks/troughs every 1s)
    assert analysis.avg_peak_distance == pytest.approx(1.0, abs=0.1), "Average peak distance of eulidian norm should be approximately 1 second."
    assert analysis.avg_trough_distance == pytest.approx(1.0, abs=0.1), "Average trough distance of eulidian norm should be approximately 1 second."

    # Check that standard deviations are near zero (since data is clean sine wave)
    assert analysis.std_dev_peak_distance < 0.05, "Standard deviation of peak distances should be near zero."
    assert analysis.std_dev_trough_distance < 0.05, "Standard deviation of trough distances should be near zero."


def test_identify_peaks_no_data(test_client: FlaskClient):
    """
    GIVEN a non-existent AssessmentStageData ID
    WHEN the identify_peaks function is called
    THEN a ValueError is raised indicating the data was not found.
    """
    # Get a non-existent ID by adding 1 to the current max ID
    non_existent_id = (db.session.query(db.func.max(AssessmentStageData.id)).scalar() or 0) + 1

    with pytest.raises(ValueError) as excinfo:
        identify_peaks(non_existent_id)
    
    assert f"AssessmentStageData with ID {non_existent_id} not found." in str(excinfo.value)

def test_identify_peaks_celery_integration(test_client: FlaskClient, sample_assessment_stage_data: AssessmentStageData):
    """
    GIVEN a sample AssessmentStageData with sinusoidal data
    WHEN the identify_peaks Celery task is called
    THEN peaks and troughs are correctly identified and stored in the database.
    """
    identifier = identify_peaks.delay(sample_assessment_stage_data.id)

    # Wait for the task to complete
    result = identifier.get(timeout=10)

    assert result is None, "The Celery task should return None."

    # Retrieve the updated ZeroCrossingAnalysis from the database
    analysis: ZeroCrossingAnalysis = ZeroCrossingAnalysis.query.filter_by(
        stage_data_id=sample_assessment_stage_data.id
    ).first()
   
    assert analysis is not None, "ZeroCrossingAnalysis should be created."
    assert len(analysis.peak_indices) > 0, "There should be detected peak indices."
    assert len(analysis.trough_indices) > 0, "There should be detected trough indices."
    
    # Check that average distances are 2 seconds apart (since period is 2s, peaks/troughs every 1s)
    assert analysis.avg_peak_distance == pytest.approx(1.0, abs=0.1), "Average peak distance of eulidian norm should be approximately 1 second."
    assert analysis.avg_trough_distance == pytest.approx(1.0, abs=0.1), "Average trough distance of eulidian norm should be approximately 1 second."

    # Check that standard deviations are near zero (since data is clean sine wave)
    assert analysis.std_dev_peak_distance < 0.05, "Standard deviation of peak distances should be near zero."
    assert analysis.std_dev_trough_distance < 0.05, "Standard deviation of trough distances should be near zero."

def test_identify_peaks_under_threshold(test_client: FlaskClient):
    """
    GIVEN a sample AssessmentStageData with sinusoidal data all below the detection threshold
    WHEN the identify_peaks function is called
    THEN no peaks or troughs are detected and stored in the database.
    """
    stage_data = AssessmentStageData(
        stage=AssessmentStage.GAIT
    )
    
    # Add data points all below the threshold of 0.2
    fs = 100  # Sampling frequency
    total_time = 10  # Total time in seconds
    create_sinusoidal_data(stage_data, 0.1, 0.5, total_time, fs)

    db.session.add(stage_data)
    db.session.commit()
    
    # Run the peak identification task
    identify_peaks(stage_data.id)
    
    # Retrieve the updated ZeroCrossingAnalysis from the database
    analysis: ZeroCrossingAnalysis = ZeroCrossingAnalysis.query.filter_by(
        stage_data_id=stage_data.id
    ).first()
    
    assert analysis is not None, "ZeroCrossingAnalysis should be created."
    assert len(analysis.peak_indices) == 0, "There should be no detected peak indices."
    assert len(analysis.trough_indices) == 0, "There should be no detected trough indices."

    assert analysis.avg_peak_distance == 0, "Average peak distance should be zero."
    assert analysis.avg_trough_distance == 0, "Average trough distance should be zero." 

    assert analysis.std_dev_peak_distance == 0, "Standard deviation of peak distances should be zero."
    assert analysis.std_dev_trough_distance == 0, "Standard deviation of trough distances should be zero."
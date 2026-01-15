import pandas as pd
import numpy as np
from scipy.signal import lfilter

from celery_app import celery
from app.models import AssessmentStageData, ZeroCrossingAnalysis, PeakIndex, TroughIndex
from app import db

@celery.task(name="identify_peaks")
def identify_peaks(assessment_stage_data_id: int):
    """
    Celery task to identify peaks and troughs in gait assessment data and
    add peak information to the database.

    Based off the algorithm from paper: 10.1109/JSEN.2016.2603163

    Note this adds a minimum threshold of 0.2 to peak and trough detection to reduce false positives.

    Args:
        data (AssessmentStageData): The assessment stage data containing points.
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
    window_size = 20
    threshold = 0.2

    # 1. Take Euclidian norm of each row
    table['norm'] = np.linalg.norm(table[['X','Y','Z']].values, axis=1)

    # 2. DC Block
    table['rolling_norm'] = table['norm'] - table['norm'].rolling(window=window_size, min_periods=window_size).mean()

    # 3. Apply lowpass
    B = np.array([1, 2, 3, 4, 3, 2, 1]) / 16.0
    A = [1]
    table["rolling_norm_lp"] = lfilter(B, A, table["rolling_norm"])

    # 4. Implement peak detection
    zero_crossings = np.where(np.diff(np.sign(table["rolling_norm_lp"].dropna())))[0]
    peaks, troughs = [], []

    for i in range(len(zero_crossings) - 1):
        start_idx = zero_crossings[i]
        end_idx = zero_crossings[i + 1]
        segment = table["rolling_norm_lp"].iloc[start_idx:end_idx]
        
        # Get actual indices in the original table
        local_min_idx = start_idx + segment.idxmin() - segment.index[0]
        local_max_idx = start_idx + segment.idxmax() - segment.index[0]
        
        min_val = table["rolling_norm_lp"].iloc[local_min_idx]
        max_val = table["rolling_norm_lp"].iloc[local_max_idx]
        
        if abs(min_val) > abs(max_val) and abs(min_val) > threshold:
            troughs.append(local_min_idx)
        elif abs(max_val) > threshold:
            peaks.append(local_max_idx)

    # Calculate average peak interval and std deviation
    peak_rows = table.iloc[peaks]
    peak_intervals = peak_rows['Timestamp'].diff().dt.total_seconds().dropna().values
    avg_peak_distance = np.mean(peak_intervals) if len(peak_intervals) > 0 else 0
    std_dev_peak_distance = np.std(peak_intervals) if len(peak_intervals) > 0 else 0

    trough_rows = table.iloc[troughs]
    trough_intervals = trough_rows['Timestamp'].diff().dt.total_seconds().dropna().values
    avg_trough_distance = np.mean(trough_intervals) if len(trough_intervals) > 0 else 0
    std_dev_trough_distance = np.std(trough_intervals) if len(trough_intervals) > 0 else 0

    # Store results in ZeroCrossingAnalysis
    analysis = ZeroCrossingAnalysis(
        stage_data_id=data.id,
        avg_peak_distance=avg_peak_distance,
        std_dev_peak_distance=std_dev_peak_distance,
        avg_trough_distance=avg_trough_distance,
        std_dev_trough_distance=std_dev_trough_distance
    )

    # Add peaks and troughs to analysis
    for peak in peaks:
        analysis.peak_indices.append(PeakIndex(index=peak))
    for trough in troughs:
        analysis.trough_indices.append(TroughIndex(index=trough))

    # Commit to database
    db.session.add(analysis)
    db.session.commit()
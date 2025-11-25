from flask import Blueprint, request, send_file, jsonify
import json
from datetime import datetime
import os
from zipfile import ZipFile
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "accel_results")

accel_test = Blueprint('accel_test', __name__)

def delete_temp_file(zip_filename: str) -> None:
    """Delete temporary file after sending."""
    try:
        os.remove(zip_filename)
    except Exception:
        pass

@accel_test.route('/test/debug/accel', methods=["POST"])
def save_acceleration_test_data():
    """
    Save acceleration test data sent from watch client as JSON file.
    """
    acceleration_data = request.get_json()
    
    # Ensure the directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Save data to a timestamped JSON file
    filename = f"accel_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(RESULTS_DIR, filename), "w") as f:
        json.dump(acceleration_data, f)
        
    return jsonify({"status": "success", "message": "Data saved", "filename": filename}), 200

@accel_test.route('/test/debug/accel', methods=["GET"])
def get_acceleration_test_data():
    """
    Provide a ZIP archive of all saved acceleration test data files.
    """
    
    # Ensure the directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    files = os.listdir(RESULTS_DIR)
    if not files:
        return "No acceleration test data available", 404
    
    # zip files and return as a downloadable archive
    filtered_files = [f for f in files if f.endswith('.json')]
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        zip_filename = tmp.name
    with ZipFile(zip_filename, 'w') as zipf:
        for file in filtered_files:
            zipf.write(os.path.join(RESULTS_DIR, file), arcname=file)
            
    # Send the zip file as a response and delete after sending
    response = send_file(zip_filename, as_attachment=True, download_name='accel_data_archive.zip', mimetype='application/zip')
    response.call_on_close(lambda: delete_temp_file(zip_filename))
    
    return response
    
    
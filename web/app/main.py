import time
from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.decorators import roles_required
from app.models import Role, PatientAssessment, Patient, User, Physician
from app.utilities.utils import get_patient_assessment_data, get_patient_information
from app.db import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    physician = False
    count = 0
    if current_user.is_authenticated:
        if current_user.has_role('Physician'):
            physician = True
            physician_profile = current_user.physician_profile
            patient_count = len(physician_profile.patients)
            return render_template('home.html', name=current_user.name, roles=current_user.roles, physician=physician, count=patient_count)
        elif current_user.has_role('Patient'):
            patient = current_user.patient_profile
            assessment_count = len(patient.assessments)
            return render_template('home.html', name=current_user.name, assessment_count=assessment_count)
        else:
            return render_template('home.html')
    else:
        return render_template('home.html')

state = 0

@main.route('/join/<experimentID>', methods=['GET'])
def joinExp(experimentID: str):
    time.sleep(1)
    global state
    state = 0
    return jsonify({'experimentID': experimentID, 'stage': 'WAITING'}), 200

@main.route('/join/<experimentID>/status', methods=['GET'])
def joinExpStatus(experimentID: str):
    global state
    if state <= 5:
        stage = "WAITING"
    elif state <= 15:
        stage = "GAIT"
    elif state <= 20:
        stage = "GAIT_COMPLETE"
    elif state <= 30:
        stage = "RT_TEST"
    else:
        stage = "COMPLETE"
    state += 1
    return jsonify({'experimentID': experimentID, 'stage': stage}), 200

@main.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    stage = data["metadata"]["stage"]
    readings = data["data"]
    # TODO: store readings in database
    return jsonify({"status": "ok"}), 200

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if request.method == 'POST':
        age = request.form['age']
        height = request.form['height']
        gender = request.form['gender']
        weight = request.form['weight']

        patient_to_update = Patient.query.filter_by(user_id=current_user.id).first()

        patient_to_update.age = age
        patient_to_update.height = height
        patient_to_update.gender = gender
        patient_to_update.weight = weight

        db.session.commit()

        return render_template('profile.html', name=current_user.name, roles=current_user.roles, age=age, height=height, gender=gender, weight=weight, patient=True)


    else:

        if current_user.has_role('Physician'):
            return render_template('profile.html', name=current_user.name, roles=current_user.roles)
        if current_user.has_role('Patient'):
            age = Patient.query.filter_by(user_id=current_user.id).first().age
            height = Patient.query.filter_by(user_id=current_user.id).first().height
            gender = Patient.query.filter_by(user_id=current_user.id).first().gender
            weight = Patient.query.filter_by(user_id=current_user.id).first().weight
            return render_template('profile.html', name=current_user.name, roles=current_user.roles, age=age, height=height, gender=gender, weight=weight, patient=True)
        else:
            return render_template('profile.html', name=current_user.name, roles=current_user.roles)

@main.route('/patient_details')
@login_required
def patient_details():
    if current_user.has_role('Physician'):
        # Find the Role object for 'Patient'
        patient_role = Role.query.filter_by(name='Patient').first()

        physician_profile = current_user.physician_profile
        if patient_role:
            # Get all users that have this role
            patients = physician_profile.patients
        else:
            patients = []

        patient_id = request.args.get('patient_id', type=int)

        if patient_id:
            results, chart_data = get_patient_assessment_data(patient_id)
            patient_user = User.query.join(Patient).filter(Patient.id == patient_id).first()
            patient_name = patient_user.name if patient_user else "Unknown"
            age, height, gender, weight = get_patient_information(patient_id)

            return render_template('specific_patient.html', name=patient_name, results=results, chart_data=chart_data, age=age, gender=gender, height=height, weight=weight)
        
        return render_template('patient_details.html', patients=patients)
    
    # If patient, redirect to specific patient page
    if current_user.patient_profile:
        patient_id = current_user.patient_profile.id

        age, height, gender, weight = get_patient_information(patient_id)

        # Show completed tests if any
        results, chart_data = get_patient_assessment_data(patient_id)

        return render_template('specific_patient.html', name=current_user.name, results=results, chart_data=chart_data, age=age, height=height, gender=gender, weight=weight)

@main.route('/all_patients', methods=['GET', 'POST'])
@roles_required('Physician')
def all_patients():
    if current_user.has_role('Physician'):
        if request.method == 'POST':
            patient_id = request.args.get('patient_id', type=int)
            patient = Patient.query.get(patient_id)
            physician = current_user.physician_profile

            if patient.physician_id:
                flash('Patient already assigned', 'warning')
            else:
                patient.physician_id = physician.id
                db.session.commit()

            return redirect(url_for('main.all_patients'))
        else:
            patients = Patient.query.options(
                db.joinedload(Patient.physician).joinedload(Physician.user)
                ).all()
            return render_template('all_patients.html', patients=patients)
    else:
        return render_template('403.html')

@main.route('/assessments', methods=['GET', 'POST'])
@login_required
def assessments():
    selected_patient_id = None
    results = []

    if current_user.has_role('Physician'):
        # Get all patients assigned to this physician
        patients = [p.user for p in current_user.physician_profile.patients if p.user is not None and p.user.patient_profile is not None]

        # If physician selects a patient
        if request.method == 'POST':
            selected_patient_id = request.form.get('patient_id')
            if selected_patient_id:
                selected_patient_id = int(selected_patient_id)
                session['selected_patient_id'] = selected_patient_id
        else:
            # use session if already set
            selected_patient_id = session.get('selected_patient_id')

        # Fetch assessments for the selected patient
        if selected_patient_id:
            results = PatientAssessment.query.filter_by(patient_id=selected_patient_id)\
                                             .order_by(PatientAssessment.date_taken.desc()).all()

        return render_template(
            'assessments.html',
            results=results,
            patients=patients,
            selected_patient_id=selected_patient_id
        )

    # If a patient is logged in, show their own assessments
    if current_user.patient_profile:
        patient_id = current_user.patient_profile.id
        results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.desc()).all()

    return render_template('assessments.html', results=results)

@main.route('/about')
def about():
    return render_template('about.html')

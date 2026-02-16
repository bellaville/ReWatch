import time
from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from zoneinfo import ZoneInfo
from app.decorators import roles_required
from app.models import Role, PatientAssessment, Patient, User
from app.utilities.utils import get_patient_assessment_data, get_patient_information
from app.db import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('home.html')

@main.route('/join/<experimentID>', methods=['GET'])
def joinExp(experimentID: str):
    time.sleep(1)
    return jsonify({'experimentID': experimentID, 'stage': 'WAITING'}), 200

state = 0

@main.route('/join/<experimentID>/status', methods=['GET'])
def joinExpStatus(experimentID: str):
    stage = "WAITING"
    global state
    if state > 5:
        stage = "GAIT"
    if state > 15:
        stage = "GAIT_COMPLETE"
    if state > 20:
        stage = "RT_TEST"
    if state > 30:
        stage = "COMPLETE"
    state += 1
    return jsonify({'experimentID': experimentID, 'stage': stage}), 200

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
            results, chart_scores, chart_avg_reactions, correct_reactions, incorrect_reactions = get_patient_assessment_data(patient_id)
            patient_user = User.query.join(Patient).filter(Patient.id == patient_id).first()
            patient_name = patient_user.name if patient_user else "Unknown"
            age, height, gender, weight = get_patient_information(patient_id)

            return render_template('specific_patient.html', name=patient_name, results=results, chart_scores=chart_scores, chart_avg_reactions=chart_avg_reactions, correct_reactions=correct_reactions, incorrect_reactions=incorrect_reactions, age=age, gender=gender, height=height, weight=weight)
        
        return render_template('patient_details.html', patients=patients)
    
    # If patient, redirect to specific patient page
    if current_user.patient_profile:
        patient_id = current_user.patient_profile.id

        age, height, gender, weight = get_patient_information(patient_id)

        # Show completed tests if any
        results, chart_scores, chart_avg_reactions, correct_reactions, incorrect_reactions = get_patient_assessment_data(patient_id)

        return render_template('specific_patient.html', name=current_user.name, results=results, chart_scores=chart_scores, chart_avg_reactions=chart_avg_reactions,correct_reactions=correct_reactions, incorrect_reactions=incorrect_reactions)

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

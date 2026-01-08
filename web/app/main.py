from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user

from app.decorators import roles_required
from app.models import Role, PatientAssessment

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('home.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, roles=current_user.roles)

@main.route('/patient_details')
@login_required
def patient_details():
    if current_user.has_role('Physician'):
        # Find the Role object for 'Patient'
        patient_role = Role.query.filter_by(name='Patient').first()

        if patient_role:
            # Get all users that have this role
            users = patient_role.users.all()
        else:
            users = []
        return render_template('patient_details.html', users=users)
    
    # If patient, redirect to specific patient page
    if current_user.patient_profile:
        patient_id = current_user.patient_profile.id
        # Show completed tests if any
        results = PatientAssessment.query.filter_by(patient_id=patient_id)\
                                         .order_by(PatientAssessment.date_taken.desc()).all()
        return render_template('specific_patient.html', name=current_user.name, results=results)

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

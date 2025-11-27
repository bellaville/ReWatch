from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user
from .decorators import roles_required
from .models import User, Role, PatientAssessment

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
@roles_required('Physician')
def patient_details():
    # Find the Role object for 'Patient'
    patient_role = Role.query.filter_by(name='Patient').first()

    if patient_role:
        # Get all users that have this role
        users = patient_role.users.all()
    else:
        users = []
    return render_template('patient_details.html', users=users)

@main.route('/assessments', methods=['GET', 'POST'])
@login_required
def assessments():
    selected_patient_id = None
    results = []

    # Check if user is a physician
    if current_user.has_role('Physician'):
        # Get list of patients assigned to this physician
        patients = [u for u in User.query.all() if not u.has_role('Physician')]

        # Physician selects patient from dropdown
        if request.method == 'POST':
            selected_patient = request.form.get('patient_id')
            if not selected_patient:
                return redirect(url_for('main.assessments'))

            selected_patient_id = int(selected_patient)
            session['selected_patient_id'] = selected_patient_id
        else:
            # for GET request, always show the placeholder by default
            selected_patient_id = None

        # If patient is selected, fetch their past results
        if selected_patient_id:
            results = PatientAssessment.query.filter_by(patient_id=selected_patient_id)\
                                             .order_by(PatientAssessment.date_taken.desc()).all()
        
        return render_template('assessments.html', results=results, patients=patients, selected_patient_id=selected_patient_id)

    # Logged-in user is a patient, show their own past results
    results = PatientAssessment.query.filter_by(patient_id=current_user.id).order_by(PatientAssessment.date_taken.desc()).all()
    return render_template('assessments.html', results=results)


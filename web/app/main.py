from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .decorators import roles_required
from .models import User, Role

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

@main.route('/assessments')
@login_required
def assessments():
    return render_template('assessments.html')


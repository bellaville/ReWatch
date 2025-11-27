from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .decorators import roles_required

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
    return render_template('patient_details.html')

@main.route('/assessments')
@login_required
def assessments():
    return render_template('assessments.html')


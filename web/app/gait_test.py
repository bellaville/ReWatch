from flask import Blueprint, render_template
from flask_login import login_required

gait_test = Blueprint('gait_test', __name__)


@gait_test.route('/start')
@login_required
def start():
    return render_template('start_gait.html')

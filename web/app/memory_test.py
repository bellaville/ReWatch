from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
import time, random
from app.models import PatientAssessment
from app.db import db

memory_test = Blueprint('memory_test', __name__)

##########################
# SHORT TERM MEMORY TEST #
##########################
SHAPES = ['circle', 'square', 'triangle', 'star', 'trapezoid', 'pentagon', 'hexagon']
COLOUR_LIST = ['blue', 'red', 'green', 'yellow', 'purple', 'orange', 'pink']
DEFAULT_COLOURS = {
    'circle': 'blue',
    'square': 'red',
    'triangle': 'green',
    'star': 'yellow',
    'trapezoid': 'purple',
    'pentagon': 'pink',
    'hexagon': 'orange'
}
# shape sizes (width, height)
SHAPE_SIZES = {
    'circle': (50, 50),
    'square': (50, 50),
    'triangle': (50, 50),
    'star': (50, 50),
    'trapezoid': (60, 50),
    'pentagon': (60, 60),
    'hexagon': (60, 60)
}

#############################
# RANDOMIZE SHAPE POSITIONS #
#############################
def generate_positions(shapes, frame_size=500, max_attempts=100):
    """Generate random top/left positions for shapes inside the frames
    and ensure that no shapes overlap each other
    """
    positions = []

    for shape in shapes:
        width, height = SHAPE_SIZES.get(shape, (50,50))

        for attempt in range(max_attempts):
            top = random.randint(0, frame_size - height)
            left = random.randint(0, frame_size - width)
            new_rect = (top, left, top + height, left + width)

            # check overlap
            overlap = any(
                not (
                    new_rect[2] <= existing[0] or  # bottom <= top
                    new_rect[0] >= existing[2] or  # top >= bottom
                    new_rect[3] <= existing[1] or  # right <= left
                    new_rect[1] >= existing[3]     # left >= right
                )
                for existing in positions
            )

            if not overlap:
                positions.append(new_rect)
                break
        else:
            # fallback if can't find a spot
            positions.append(new_rect)

    return [{'top': r[0], 'left': r[1]} for r in positions]

##############
# START TEST #
##############
@memory_test.route('/start')
@login_required
def start_memory_test():
    """ Initializes a short term memory test session for the current user.

    Establishes a Flask session to store temporary test metrics for a user,
    allowing the memory test to track progress and user responses
    throughout multiple rounds.
    """
    # if user is physician, use the selected patient from session
    if current_user.has_role('Physician'):
        patient_id = session.get('selected_patient_id')
    else:
        # patient is performing their own test, use their own id from db/login
        patient_id = current_user.patient_profile.id

    session['test_patient_id'] = patient_id 

    # initialize session variables
    session['round'] = 0
    session['score'] = 0
    session['reaction_times'] = []
    session['show_test'] = False # don't show the test frame yet

    memorization_time = session.get('memorization_time', 5)
    num_rounds = session.get('num_rounds', 5)

    # flash instructions
    flash(
         "<strong>THIS IS NOT A MEDICAL DIAGNOSIS!</strong><br><br>"
        f"You will see a set of shapes to memorize for {memorization_time} seconds. "
        "After that, a new set will appear. Decide if the shapes are the same or different. "
        f"Try to respond as quickly as possible as your reaction time will be recorded. There will be {num_rounds} rounds. Are you ready to start?",
        "memory_test"
    )

    return render_template('memory_test.html', show_test=False)

######################
# MEMORIZATION PHASE #
######################
@memory_test.route('/memorize')
@login_required
def memory_memorize():
    """ Memorization phase: user has a configured number of seconds to
    memorize the displayed set of shapes
    """
    num_rounds = session.get('num_rounds', 5)
    if 'round' not in session or session['round'] >= int(num_rounds):
        return redirect(url_for('memory_test.memory_result'))
    
    # load settings from session (customized by physician)
    num_shapes = session.get('num_shapes', 3)
    difficulty = session.get('difficulty', 'easy')
    memorization_time = session.get('memorization_time', 5)

    # generate shape set and assign colors
    current_shapes = random.sample(SHAPES, num_shapes)

    current_colours = []
    for shape in current_shapes:
        if difficulty == 'easy':
            # each shape always has the same distinct colour
            current_colours.append(DEFAULT_COLOURS.get(shape, 'gray'))
        else:
            # randomize colours for harder difficulty
            current_colours.append(random.choice(COLOUR_LIST))

    # generate random positions for the shapes in the test frame
    shape_positions = generate_positions(current_shapes, frame_size=500)

    # stores the original memorized set (fixed for comparison phase)
    session['previous_shapes'] = current_shapes
    session['previous_colours'] = current_colours
    # stores the set that will be shown in the response phase (which may be modified in comparison phase)
    session['current_shapes'] = current_shapes
    session['current_colours'] = current_colours

    session['shape_positions'] = shape_positions
    session['memorization_time'] = memorization_time

    return render_template('memory_memorize.html', shapes=current_shapes, round_num=session['round']+1, shape_positions=shape_positions, shape_colours=current_colours, memorization_time=session['memorization_time'] )

##################
# RESPONSE PHASE #
##################
@memory_test.route('/response', methods=['GET', 'POST'])
@login_required
def memory_test_view():
    """ Comparison phase where user responds """
    num_rounds = session.get('num_rounds', 5)
    if 'round' not in session or session['round'] >= int(num_rounds):
        return redirect(url_for('memory_test.memory_result'))

    num_shapes = session.get('num_shapes', 3)
    difficulty = session.get('difficulty', 'easy')

    if request.method == 'POST':
        # handle user's answer
        choice = request.form.get('choice')
        reaction_time = request.form.get('reaction_time', type=float)
        if reaction_time is not None:
            session['reaction_times'].append(reaction_time)

        prev_shapes= session['previous_shapes']
        prev_colours = session['previous_colours']
        curr_shapes = session['current_shapes']
        curr_colours = session['current_colours']

        if difficulty == 'easy':
            correct = set(prev_shapes) == set(curr_shapes)
        else:
            # for hard mode, check if shape AND colour match
            prev_map = dict(zip(prev_shapes, prev_colours))
            curr_map = dict(zip(curr_shapes, curr_colours))
            correct = prev_map == curr_map
        if (choice == 'Same' and correct) or (choice == 'Different' and not correct):
            session['score'] += 1

        session['round'] += 1
        return redirect(url_for('memory_test.memory_memorize'))  # start next memorization round

    # GET request: show comparison phase
    prev_shapes = session['previous_shapes']
    prev_colours = session['previous_colours']

    # 50% chance to show same or new set
    if random.random() < 0.5:
        current_shapes = prev_shapes.copy()
        current_colours = prev_colours.copy()
    else:
        current_shapes = random.sample(SHAPES, num_shapes)
        # assign colours
        current_colours = [
            DEFAULT_COLOURS.get(shape, 'gray') if difficulty == 'easy' else random.choice(COLOUR_LIST)
            for shape in current_shapes
        ]

    # generate positions
    shape_positions = generate_positions(current_shapes, frame_size=500)

    # save for template and reaction timing
    session['current_shapes'] = current_shapes
    session['current_colours'] = current_colours
    session['shape_positions'] = shape_positions

    return render_template(
        'memory_test.html',
        shapes=current_shapes,
        round_num=session['round'] + 1,
        buttons_enabled=True,
        show_test=True,
        shape_positions=shape_positions,
        shape_colours=current_colours
    )

################
# RESULTS PAGE #
################
@memory_test.route('/result')
@login_required
def memory_result():
    avg_reaction = sum(session.get('reaction_times', [])) / max(len(session.get('reaction_times', [])), 1)
    score = session.get('score', 0)
    total_rounds = session.get('num_rounds', 5)

    # use the patient ID stored in the session (set by the physician selecting the patient)
    patient_id = session.get('test_patient_id')
    if not patient_id:
        # check if currently logged-in user is a patient, if so, use their own id
        if current_user.patient_profile:
            patient_id = current_user.patient_profile.id
        else:
            return redirect(url_for('main.index'))

    result = PatientAssessment(
            patient_id=patient_id,
            score=score,
            total_rounds=total_rounds,
            avg_reaction_time=avg_reaction,
    )
    db.session.add(result)
    db.session.commit()

    return render_template('memory_result.html', score=score, avg_reaction=avg_reaction, total_rounds=int(total_rounds))

######################
# CUSTOMIZATION PAGE #
######################
@memory_test.route("/customize", methods=['GET', 'POST'])
@login_required
def memory_test_customization():
    """Page for physician to configure short-term memory test settings
    """
    if request.method == "POST":
        # store physician's inputted customization in session
        session['num_shapes'] = int(request.form.get('num_shapes', 3))
        session['memorization_time'] = int(request.form.get('memorization_time', 5))
        session['difficulty'] = request.form.get('difficulty', 'easy') # easy or hard
        session['num_rounds'] = request.form.get('num_rounds', 5)
        return redirect(url_for('memory_test.start_memory_test')) # go to flash instruction message
    
    # show default customization values as a dictionary for easier unpacking in html (GET request)
    defaults = {
        'num_shapes': session.get('num_shapes', 3),
        'memorization_time': session.get('memorization_time', 5),
        'difficulty': session.get('difficulty', 'easy'),
        'num_rounds': session.get('num_rounds', 5)
    }

    return render_template('memory_customization.html', **defaults)

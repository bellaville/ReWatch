from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
import time, random
from app.models import AssessmentStage, AssessmentStageData, PatientAssessment, Physician
from app.db import db

memory_test = Blueprint('memory_test', __name__)

##########################
# SHORT TERM MEMORY TEST #
##########################
SHAPES = ['circle', 'square', 'triangle', 'star', 'trapezoid', 'pentagon', 'hexagon']
COLOUR_LIST = ['blue', 'red', 'green', 'gold', 'purple', 'orange', 'pink']
DEFAULT_COLOURS = {
    'circle': 'blue',
    'square': 'red',
    'triangle': 'green',
    'star': 'gold',
    'trapezoid': 'purple',
    'pentagon': 'pink',
    'hexagon': 'orange'
}

############################
# HELPER TO GET ASSESSMENT #
############################
def fetch_assessment(join_code: str, cur_step: int | None = None) -> PatientAssessment | None:
    """
    Gets assessment given a join code and optional cur_step
    """
    if cur_step:
        return db.session.query(PatientAssessment).filter(PatientAssessment.is_running == True, PatientAssessment.join_code == join_code, PatientAssessment.current_step == PatientAssessment.STEP_ORDER.index(cur_step)).first()
    return db.session.query(PatientAssessment).filter(PatientAssessment.is_running == True, PatientAssessment.join_code == join_code).first()


##############
# START TEST #
##############
@memory_test.route('/start', methods=["GET"])
@login_required
def start_memory_test():
    """ Initializes a short term memory test session for the current user.

    Establishes a Flask session to store temporary test metrics for a user,
    allowing the memory test to track progress and user responses
    throughout multiple rounds.
    """
    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.GAIT_COMPLETE)
    
    if not assessment:
        return jsonify({"success": False, "error": "Could not find assessment"}), 400   

    # initialize session variables
    session['round'] = 1
    session['reaction_records'] = []

    return render_template('memory_display_warning.html', memorization_time=assessment.memorization_time, num_rounds=assessment.total_rounds)


@memory_test.route('/start', methods=["POST"])
@login_required
def confirm_start_memory_test():
    """ 
    Initializes a short term memory test session for the current user.

    Establishes a Flask session to store temporary test metrics for a user,
    allowing the memory test to track progress and user responses
    throughout multiple rounds.
    """
    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.GAIT_COMPLETE)
    
    if not assessment:
        return jsonify({"success": False, "error": "Could not find assessment"}), 400   
    
    assessment.increment_step()

    return jsonify({"success": True }), 200

#################
# CONNECT WATCH #
#################
@memory_test.route('/connect', methods = ["GET"])
@login_required
def connect_watch_page():
    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.WAITING)

    if not assessment:
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    return render_template('memory_connect_watch.html', join_code = session['join_code'])

@memory_test.route('/connect', methods = ["POST"])
@login_required
def connect_watch_check():
    if not request.json or not request.json.get("join_code"):
        return jsonify({"status": False, "error": "Could not find join_code"}), 400
    
    assessment = fetch_assessment(session["join_code"])
    return jsonify({"status": assessment.watch_connected}), 200
    
###################
# WATCH ENDPOINTS #
###################

@memory_test.route('/connect/<join_code>', methods = ["POST"])
def connect_add_watch(join_code: str):   
    assessment = fetch_assessment(join_code)
    assessment.watch_connected = True
    db.session.commit()
    return jsonify({"experimentID": assessment.join_code, "stage": assessment.get_current_step()}), 200

@memory_test.route('/<join_code>/status', methods = ["GET"])
def watch_get_status(join_code: str):   
    assessment = fetch_assessment(join_code)
    return jsonify({"experimentID": assessment.join_code, "stage": assessment.get_current_step()}), 200

@memory_test.route('/<join_code>/<stage>/upload', methods = ["POST"])
def watch_upload_data(join_code: str, stage: str):   
    stage = AssessmentStage(stage)
    assessment = fetch_assessment(join_code)
    json_body = request.json
    assessment_data = AssessmentStageData.from_json(json_body, stage, assessment.id)
    
    # If its at complete, finalize and set running to false
    if (assessment.get_current_step() == AssessmentStage.COMPLETE.value):
        assessment.is_running = False
        db.session.add(assessment)

    db.session.add(assessment_data)
    db.session.commit()

    if not assessment.is_running:
        assessment.run_celery_tasks()

    return jsonify({"success": True}), 200

#################
# GAIT ANALYSIS #
#################
@memory_test.route('/gait', methods = ["POST"])
@login_required
def begin_gait():
    if not request.json or not request.json.get("join_code"):
        return jsonify({"status": False, "error": "Could not find join_code"}), 400
    
    assessment = fetch_assessment(request.json.get("join_code"), AssessmentStage.WAITING)
    
    if not assessment:
        return jsonify({"success": False, "error": "Could not find assessment"}), 400
    
    assessment.increment_step()
    
    return jsonify({"success": True}), 200

@memory_test.route('/gait_complete', methods = ["POST"])
@login_required
def end_gait():
    if not request.json or not request.json.get("join_code"):
        return jsonify({"status": False, "error": "Could not find join_code"}), 400
    
    assessment = fetch_assessment(request.json.get("join_code"), AssessmentStage.GAIT)
    
    if not assessment:
        return jsonify({"success": False, "error": "Could not find assessment"}), 400
    
    assessment.increment_step()

    return redirect(url_for('memory_test.start_memory_test'))

###################
# TIME SYNC PHASE #
###################
@memory_test.route('/time/sync', methods=["POST"])
def receive_sync_request():
    receive_time = round(time.time_ns())

    if not request.json or not request.json.get("join_code"):
        return jsonify({"status": False, "error": "Could not find join_code"}), 400
    
    assessment = fetch_assessment(request.json.get("join_code"), AssessmentStage.RT_TEST)

    if not assessment:
        return jsonify({"error": "Assessment could not be found"}), 404
    
    assessment.increment_synchronization(request.json['device'])

    return jsonify({"timing2": receive_time, "timing3": round(time.time_ns())}), 200

@memory_test.route('/time/request_future', methods=["POST"])
def give_synched_timing():

    if not request.json or not request.json.get("join_code"):
        return jsonify({"status": False, "error": "Could not find join_code"}), 400
    
    assessment = fetch_assessment(request.json.get("join_code"), AssessmentStage.RT_TEST)

    if assessment.can_create_test_time():
        return jsonify({"delay": assessment.get_test_start()}), 200
    else:
        return jsonify({"error": "Cannot start test yet"}), 206

######################
# MEMORIZATION PHASE #
######################
@memory_test.route('/memorize')
@login_required
def memory_run_test():
    """ Memorization phase: user has a configured number of seconds to
    memorize the displayed set of shapes
    """
    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.RT_TEST)

    if not assessment:
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))
    
    # generate shape set and assign colors
    memorized_shapes = random.sample(SHAPES, assessment.num_shapes)

    memorized_colours = []
    for shape in memorized_shapes:
        if assessment.difficulty == 'Easy':
            # each shape always has the same distinct colour
            memorized_colours.append(DEFAULT_COLOURS.get(shape, 'gray'))
        else:
            # randomize colours for harder difficulty
            memorized_colours.append(random.choice(COLOUR_LIST))
    
    # Generate test set
    if random.random() < 0.5:
        test_shapes = memorized_shapes
        test_colours = memorized_colours
        session['correct'] = "Same"
    else:
        test_shapes = random.sample(SHAPES, assessment.num_shapes)
        # assign colours
        test_colours = [
            DEFAULT_COLOURS.get(shape, 'gray') if assessment.difficulty == 'Easy' else random.choice(COLOUR_LIST)
            for shape in test_shapes
        ]
        session['correct'] = "Different"

    return render_template('memory_run_test.html', test_shapes=test_shapes, test_colours=test_colours, 
                           memorized_shapes=memorized_shapes, memorized_colours=memorized_colours, 
                           round_num=session['round'], memorization_time=assessment.memorization_time, join_code=assessment.join_code)

##################
# RESPONSE PHASE #
##################
@memory_test.route('/response', methods=['POST'])
@login_required
def memory_test_view():
    """
    Route that recieves the user response and progresses the assessment with
    either another test or by showing the results
    """

    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.RT_TEST)

    if not assessment:
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    # handle user's answer
    reaction_time = request.form.get('reaction_time', type=float)
    choice = request.form.get('choice')

    if session["correct"] == choice:
        assessment.score += 1
        db.session.commit()

    if reaction_time is not None:
        session['reaction_records'].append({
            "time": reaction_time,
            "correct": session["correct"] == choice,
            "num_shapes": assessment.num_shapes,
        })

    session['round'] += 1

    if session["round"] > assessment.total_rounds:
        return redirect(url_for('memory_test.memory_result'))

    return redirect(url_for('memory_test.memory_run_test'))  # start next memorization round

################
# RESULTS PAGE #
################
@memory_test.route('/result', methods=["GET"])
@login_required
def memory_result():

    if not session.get("join_code"):
        return redirect(url_for('memory_test.confirm_memory_test_configuration'))

    assessment = fetch_assessment(session["join_code"], AssessmentStage.RT_TEST)
    
    if not assessment:
        return jsonify({"error": "Could not find assessment"}), 404

    reaction_records = session.get('reaction_records', [])
    avg_reaction = sum(r["time"] for r in reaction_records) / max(len(reaction_records), 1)

    assessment.avg_reaction_time = avg_reaction
    assessment.reaction_records = reaction_records
    assessment.memory_accuracy = (assessment.score/assessment.total_rounds)*100

    assessment.increment_step()

    return render_template('memory_result.html', score=assessment.score, avg_reaction=avg_reaction, total_rounds=assessment.total_rounds, memory_accuracy=assessment.memory_accuracy)

######################
# CUSTOMIZATION PAGE #
######################
@memory_test.route("/customize", methods=['GET'])
@login_required
def memory_test_customization():
    """
    Page for physician to configure short-term memory test settings
    """    
    # show default customization values as a dictionary for easier unpacking in html (GET request)
    defaults = {
        'num_shapes': 3,
        'memorization_time': 3,
        'difficulty': "Easy",
        'num_rounds': 5
    }

    selected_id = None

    if current_user.has_role('Physician'):
        patients = [p.user for p in current_user.physician_profile.patients if p.user is not None and p.user.patient_profile is not None] 
        if patients:
            selected_id = patients[0].patient_profile.id

    else:
        patients = []
        selected_id = current_user.id


    return render_template('memory_customization.html', **defaults, patients=patients, selected_id=selected_id)


@memory_test.route("/customize", methods=['POST'])
@login_required
def confirm_memory_test_configuration():
    """
    POST endpoint to create initial assessment and begin steps
    """    

    if current_user.has_role('Physician'):
        # if user is physician, use the selected patient from session
        patient_id = int(request.form['patient_id'])
        if patient_id not in [p.id for p in db.session.get(Physician, current_user.physician_profile.id).patients]:
            return memory_test_customization()
    else:
        # patient is performing their own test, use their own id from db/login
        patient_id = current_user.patient_profile.id
            
    # Start assessment tracking in DB
    assessment = PatientAssessment(
        patient_id=patient_id,
        score=0,
        total_rounds=request.form["num_rounds"],
        avg_reaction_time=0,
        difficulty=request.form['difficulty'],
        reaction_records=[],
        is_running=True,
        watch_connected=False,
        current_step = 0,
        memorization_time=request.form['memorization_time'],
        num_shapes=request.form["num_shapes"]
    )        

    db.session.add(assessment)
    db.session.commit()
    
    session['join_code'] = assessment.join_code
    
    return redirect(url_for('memory_test.connect_watch_page')) 

#################
# PRACTICE TEST #
#################
@memory_test.route('/practice')
@login_required
def practice_memory_test():
    """
    Practice memory test with no watch dependency, no DB saving, and using default settings
    """
    memorized_shapes = random.sample(SHAPES, 3) # default 3 shapes
    memorized_colours = [DEFAULT_COLOURS[shapes] for shapes in memorized_shapes]

    if random.random() < 0.5:
        test_shapes = memorized_shapes
        test_colours = memorized_colours
        session['practice_correct'] = "Same"
    else:
        test_shapes = random.sample(SHAPES, 3)
        test_colours = [DEFAULT_COLOURS[shapes] for shapes in test_shapes]
        session['practice_correct'] = "Different"

    return render_template('memory_practice.html',
                           memorized_shapes = memorized_shapes,
                           memorized_colours=memorized_colours,
                           test_shapes=test_shapes,
                           test_colours=test_colours,
                           memorization_time=3)

@memory_test.route('/practice/response', methods=['POST'])
@login_required
def practice_response():
    """
    Handles the practice round responses, just shows the results, no DB saving
    """
    choice = request.form.get('choice')
    correct = session.get('practice_correct')
    was_correct = choice == correct

    return render_template('memory_practice_result.html',
                           was_correct=was_correct,
                           correct_answer = correct)
                           
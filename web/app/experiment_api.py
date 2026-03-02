from flask import Blueprint, abort, jsonify

experiment_bp = Blueprint("experiment_api", __name__, url_prefix="/join")

def get_experiment_from_db(experiment_id: str):
    # TODO: replace with real DB lookup
    # Return None if experiment does not exist
    return {
        "experimentID": experiment_id,
        "name": "Stubbed experiment",
        "description": "This is a placeholder experiment object.",
        "status": "PENDING",  # or "JOINED", "REJECTED", etc.
    }


def get_join_status_from_db(experiment_id: str):
    # TODO: replace with real DB lookup for join status
    return {
        "experimentID": experiment_id,
        "status": "PENDING",  # update according to your state machine
        "joinedAt": None,
    }


@experiment_bp.route("/<experiment_id>", methods=["GET"])
def join_experiment(experiment_id):
    experiment = get_experiment_from_db(experiment_id)
    if experiment is None:
        abort(404)
    # Shape this to match your JoinedExperiment Kotlin data class
    return jsonify(experiment)


@experiment_bp.route("/<experiment_id>/status", methods=["GET"])
def poll_status(experiment_id):
    status = get_join_status_from_db(experiment_id)
    if status is None:
        abort(404)
    # Shape this to match your JoinedExperiment Kotlin data class
    return jsonify(status)
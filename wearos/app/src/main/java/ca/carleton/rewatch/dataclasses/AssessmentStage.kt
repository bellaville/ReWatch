package ca.carleton.rewatch.dataclasses

sealed class AssessmentStage(val stage: String) {
    object WAITING : AssessmentStage("WAITING")
    object CALIBRATION : AssessmentStage("GAIT")
}
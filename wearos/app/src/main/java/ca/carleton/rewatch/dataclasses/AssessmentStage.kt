package ca.carleton.rewatch.dataclasses

sealed class AssessmentStage(val stage: String) {
    object WAITING : AssessmentStage("WAITING")
    object CALIBRATION : AssessmentStage("GAIT")
    object CALIBRATION_COMPLETE: AssessmentStage("GAIT_COMPLETE")
    object RT_TEST: AssessmentStage("RT_TEST")
    object COMPLETE: AssessmentStage("COMPLETE")
}
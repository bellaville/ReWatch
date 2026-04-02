package ca.carleton.rewatch.dataclasses

/**
 * Data class to hold received information about the experiment joined on the watch
 *
 * @param experimentID The id of the experiment
 * @param stage The current stage of the assessment
 */
data class JoinedExperiment(
    val experimentID: String,
    val stage: String
)
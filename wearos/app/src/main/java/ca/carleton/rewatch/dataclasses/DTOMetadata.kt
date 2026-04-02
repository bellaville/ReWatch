package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

/**
 * Used for storing the metadata that will be transferred to the web app
 *
 * @param stage The stage of the assessment
 * @param trial Optional attribute to store the current trial number
 * @param memStep Optional attribute to store the current step of the memory test
 */
@Serializable
data class DTOMetadata(
    val stage: String,
    val trial: Int? = null,
    val memStep: Int? = null,
)

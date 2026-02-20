package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

@Serializable
data class DTOMetadata(
    val step: String, // @TODO Change to an enum (AssessmentStage?)
    val trial: Int? = null,
)

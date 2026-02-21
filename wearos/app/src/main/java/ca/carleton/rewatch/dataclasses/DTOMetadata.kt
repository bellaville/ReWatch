package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

@Serializable
data class DTOMetadata(
    val stage: String,
    val trial: Int? = null,
    val memStep: Int? = null,
)

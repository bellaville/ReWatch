package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

@Serializable
/**
 * Used to package data sent to the ReWatch web application
 */
data class SensorDTO(
    val metadata: DTOMetadata,
    val data: List<SensorReading>,
)

package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

@Serializable
/**
 * Used to package data sent to the ReWatch web application
 *
 * @param metadata Data that is used to identify the data sent
 * @param data The data points recorded from accelerometer
 */
data class SensorDTO(
    val metadata: DTOMetadata,
    val data: List<SensorReading>,
)

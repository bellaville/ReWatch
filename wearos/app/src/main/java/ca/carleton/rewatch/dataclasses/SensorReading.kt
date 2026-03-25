package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
/**
 * Used to hold the reading from the accelerometer for a specific time.
 */
data class SensorReading(
    @SerialName("ts") val timestamp: Long,
    val x: Float,
    val y: Float,
    val z: Float
)
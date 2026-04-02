package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
/**
 * Used to hold the reading from the accelerometer for a specific time.
 *
 * @param timestamp the timestamp for this set of data
 * @param x the x value of the accelerometer
 * @param y the y value of the accelerometer
 * @param z the z value of the accelerometer
 */
data class SensorReading(
    @SerialName("ts") val timestamp: Long,
    val x: Float,
    val y: Float,
    val z: Float
)
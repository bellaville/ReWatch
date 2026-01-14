package ca.carleton.rewatch.dataclasses

/**
 * Used to hold the reading from the accelerometer for a specific time.
 */
data class SensorReading(
    val timestamp: Long,
    val x: Float,
    val y: Float,
    val z: Float
)
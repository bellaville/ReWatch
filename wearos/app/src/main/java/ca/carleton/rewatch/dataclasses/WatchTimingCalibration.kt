package ca.carleton.rewatch.dataclasses

/**
 * Timing values for calibration of the watch
 */
data class WatchTimingCalibration(
    var timing1: Long = 0.toLong(),
    var timing2: Long = 0.toLong(),
    var timing3: Long = 0.toLong(),
    var timing4: Long = 0.toLong(),
)

/**
 * Used for transferring the average delay in device calibration
 *
 * @param join_code The code used to join the experiment
 * @param delay the average timing delay
 */
data class AverageTimingDelay(
    val join_code: String,
    val delay: Long
)

/**
 * Used for measuring the average timing delay
 *
 * @param join_code the code used to join the experiment
 * @param device the device being calibrated
 */
data class MeasureTimingDelay(
    val join_code: String,
    val device: String = "watch"
)

/**
 * Calculates the average timing delay in watch calibration
 */
fun calculateAverageTimingDelay(watchTimingCalibration: WatchTimingCalibration): Long {
    val t2Ms = watchTimingCalibration.timing2 / 1_000_000
    val t3Ms = watchTimingCalibration.timing3 / 1_000_000

    return ((t2Ms - watchTimingCalibration.timing1) + (watchTimingCalibration.timing4 - t3Ms)) / 2
}
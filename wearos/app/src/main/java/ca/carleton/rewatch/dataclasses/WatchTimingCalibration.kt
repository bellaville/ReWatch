package ca.carleton.rewatch.dataclasses

data class WatchTimingCalibration(
    var timing1: Long = 0.toLong(),
    var timing2: Long = 0.toLong(),
    var timing3: Long = 0.toLong(),
    var timing4: Long = 0.toLong(),
)

data class AverageTimingDelay(
    val join_code: String,
    val delay: Long
)

data class MeasureTimingDelay(
    val join_code: String,
    val device: String = "watch"
)

fun calculateAverageTimingDelay(watchTimingCalibration: WatchTimingCalibration): Long {
    val t2Ms = watchTimingCalibration.timing2 / 1_000_000
    val t3Ms = watchTimingCalibration.timing3 / 1_000_000

    return ((t2Ms - watchTimingCalibration.timing1) + (watchTimingCalibration.timing4 - t3Ms)) / 2
}
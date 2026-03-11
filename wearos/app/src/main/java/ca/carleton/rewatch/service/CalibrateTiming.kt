package ca.carleton.rewatch.service

import android.util.Log
import ca.carleton.rewatch.dataclasses.AverageTimingDelay
import ca.carleton.rewatch.dataclasses.MeasureTimingDelay
import ca.carleton.rewatch.dataclasses.calculateAverageTimingDelay
import kotlinx.coroutines.delay
import kotlin.time.Clock
import kotlin.time.ExperimentalTime


@OptIn(ExperimentalTime::class)
suspend fun timingHandshake(experimentID: String): Long {

    val delays = Array<Long>(10,  { 0 })
    val measureTimingDelay = MeasureTimingDelay(experimentID)
    for (i in 0..9) {
        val start = Clock.System.now()
        val watchTimingCalibration = Requestor.getSensorService().calibrateWatchTiming(measureTimingDelay)
        val end = Clock.System.now()
        watchTimingCalibration.timing1 = start.toEpochMilliseconds()
        watchTimingCalibration.timing4 = end.toEpochMilliseconds()
        delays[i] = calculateAverageTimingDelay(watchTimingCalibration)
    }

    val avgDelay = AverageTimingDelay(experimentID, delays.average().toLong())
    val handshakes = Array<Long>(5, { 0 })

    for (i in 0..4) {
        var handshakeTiming = Requestor.getSensorService().obtainFutureTiming(avgDelay)
        while (handshakeTiming.code() == 206) {
            delay(1000);
            handshakeTiming = Requestor.getSensorService().obtainFutureTiming(avgDelay)
        }
        handshakes[i] = Clock.System.now().toEpochMilliseconds() + (handshakeTiming.body()?.delay ?: 0);
    }

    handshakes.sort();
    return handshakes[2] - Clock.System.now().toEpochMilliseconds() - avgDelay.delay;
}
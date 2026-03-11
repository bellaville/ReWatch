package ca.carleton.rewatch.service

import ca.carleton.rewatch.dataclasses.AverageTimingDelay
import ca.carleton.rewatch.dataclasses.MeasureTimingDelay
import ca.carleton.rewatch.dataclasses.SensorDTO
import ca.carleton.rewatch.dataclasses.WatchTimingCalibration
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

interface SendAccelerometerData {
    @POST("/assessments/memory_test/{experimentID}/{state}/upload")
    suspend fun uploadSensorData(@Path("experimentID") experimentID: String, @Path("state") state: String, @Body data: SensorDTO): Response<Unit>

    @POST("/assessments/memory_test/time/sync")
    suspend fun calibrateWatchTiming(@Body measureTimingDelay: MeasureTimingDelay): WatchTimingCalibration

    @POST("/assessments/memory_test/time/request_future")
    suspend fun obtainFutureTiming(@Body averageTimingDelay: AverageTimingDelay): Response<AverageTimingDelay>
}
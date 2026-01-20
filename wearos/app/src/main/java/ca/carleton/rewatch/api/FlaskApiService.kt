package ca.carleton.rewatch.api

import ca.carleton.rewatch.dataclasses.SensorReading
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface FlaskApiService {
    @POST("upload")
    suspend fun uploadReadings(@Body readings: List<SensorReading>): Response<Unit>
}
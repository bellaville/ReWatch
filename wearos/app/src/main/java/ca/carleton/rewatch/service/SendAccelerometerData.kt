package ca.carleton.rewatch.service

import ca.carleton.rewatch.dataclasses.SensorDTO
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

interface SendAccelerometerData {
    @POST("/assessments/memory_test/{experimentID}/{state}/upload")
    suspend fun uploadSensorData(@Path("experimentID") experimentID: String, @Path("state") state: String, @Body data: SensorDTO): Response<Unit>
}
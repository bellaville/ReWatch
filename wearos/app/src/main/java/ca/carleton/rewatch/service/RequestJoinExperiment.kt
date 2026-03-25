package ca.carleton.rewatch.service

import ca.carleton.rewatch.dataclasses.JoinedExperiment
import com.google.android.gms.common.api.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * Interface that gets parsed into web request
 *
 * CREDIT: https://square.github.io/retrofit/
 */
interface RequestJoinExperiment {

    @POST("/assessments/memory_test/connect/{experimentID}")
    suspend fun join(@Path("experimentID") experimentID: String): JoinedExperiment

    @GET("/assessments/memory_test/{experimentID}/status")
    suspend fun pollStatus(@Path("experimentID") experimentID: String): JoinedExperiment
}
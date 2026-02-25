package ca.carleton.rewatch.service

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/**
 * Singleton object that gets called to submit web requests
 *
 * CREDIT: https://square.github.io/retrofit/
 */
object Requestor {

    val baseUrl = "http://192.168.2.13:5000/"
    private val _instance: RequestJoinExperiment = Retrofit.Builder().baseUrl(baseUrl).addConverterFactory(GsonConverterFactory.create()).build().create(
        RequestJoinExperiment::class.java
    )

    fun getInstance(): RequestJoinExperiment {
        return _instance
    }

}
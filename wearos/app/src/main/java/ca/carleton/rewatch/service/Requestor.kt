package ca.carleton.rewatch.service

import ca.carleton.rewatch.BuildConfig
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/**
 * Singleton object that gets called to submit web requests
 *
 * CREDIT: https://square.github.io/retrofit/
 */
object Requestor {

    //val baseUrl = "http://192.168.2.32:5000/"
    val baseUrl = BuildConfig.API_ENDPOINT

    private val retrofit = Retrofit.Builder().baseUrl(baseUrl).addConverterFactory(
        GsonConverterFactory.create()).build()

    private val _joinInstance: RequestJoinExperiment = retrofit.create(RequestJoinExperiment::class.java)

    private val _dataInstance: SendAccelerometerData = retrofit.create(SendAccelerometerData::class.java)

    fun getInstance(): RequestJoinExperiment = _joinInstance

    fun getSensorService(): SendAccelerometerData = _dataInstance


}
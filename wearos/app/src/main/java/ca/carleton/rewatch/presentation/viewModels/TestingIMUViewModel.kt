package ca.carleton.rewatch.presentation.viewModels

import android.app.Application
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavController
import ca.carleton.rewatch.dataclasses.AssessmentStage
import ca.carleton.rewatch.dataclasses.DTOMetadata
import ca.carleton.rewatch.dataclasses.JoinedExperiment
import ca.carleton.rewatch.dataclasses.SensorDTO
import ca.carleton.rewatch.presentation.AccelerometerManager
import ca.carleton.rewatch.presentation.Screen
import ca.carleton.rewatch.service.Requestor
import ca.carleton.rewatch.service.timingHandshake
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class TestingIMUViewModel(application: Application) : AndroidViewModel(application) {
    private val sensorManager = AccelerometerManager(application)

    fun startCollection() {
        sensorManager.start();
    }

    fun stopCollection() {
        if (sensorManager.isRunning()) {
            sensorManager.stop()
            uploadCollectedData();
        }
    }

    fun changeCollection() {
        if (sensorManager.isRunning()) {
            stopCollection()
        } else {
            startCollection();
        }
    }


    fun uploadCollectedData() {
        viewModelScope.launch {
            try {
                val metadata = DTOMetadata("Test")
                val dataToUpload = SensorDTO(metadata, sensorManager.recordedData)

                val response = Requestor.getSensorService().uploadTestSensorData(
                    data = dataToUpload
                )

                if (response.isSuccessful) {
                    Log.d("Upload", "Data successfully sent to server!")
                } else {
                    Log.e("Upload", "Server error: ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e("Upload", "Network failure", e)
            }
        }
    }
}

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

class RTTestViewModel(application: Application, private val savedStateHandle: SavedStateHandle) : AndroidViewModel(application) {

    private val sensorManager = AccelerometerManager(application)
    var collectionText by mutableStateOf("Awaiting Reaction Time Test Start")
    var circleColour by mutableIntStateOf(0)

    fun startCollection() {
        sensorManager.start()
        circleColour = 1;
    }

    fun stopCollection(experimentID: String, stage: String) {
        if (sensorManager.isRunning()) {
            sensorManager.stop()
            uploadCollectedData(experimentID, stage)
        }
        circleColour = 0;
    }

    fun startTimeSync() {
        viewModelScope.launch {
            var experimentID = savedStateHandle["experimentID"] ?: ""
            var retries = 0
            while (true) {
                try {
                    var timing = timingHandshake(experimentID)
                    Log.d("TIMING", timing.toString())
                    delay(timing)
                    startCollection();
                    delay(5000)
                    stopCollection(experimentID, AssessmentStage.RT_TEST.stage)
                } catch (e: Exception) {
                    retries += 1;
                    if (retries >= 3) {
                        return@launch
                    }
                }
            }
        }
    }

    /**
     * Builds and sends poll request to ReWatch web server
     *
     * @return Optional JoinedExperiment, or null if request failed
     */
    suspend fun sendRequest(experimentID: String): JoinedExperiment? {
        return try {
            Requestor.getInstance().pollStatus(experimentID)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Polls the experiment in a coroutine to the webserver,
     * and takes appropriate action based on request result
     */
    fun pollExperiment(navController: NavController) {
        val experimentID: String = savedStateHandle["experimentID"] ?: ""

        if (experimentID == "") {
            navController.navigate(Screen.JoinExperiment.route)
            return
        }

        viewModelScope.launch {
            var isAwaiting = true

            // Loop to check status every second
            while (isAwaiting) {
                var joinedExperiment: JoinedExperiment? = sendRequest(experimentID)

                // If null, return to join experiment and stop
                if (joinedExperiment == null) {
                    navController.navigate(Screen.JoinExperiment.route)
                    return@launch
                }

                // Check if current stage, if not navigate to next stage
                if (joinedExperiment.stage == AssessmentStage.RT_TEST.stage) {
                    Log.d("EXPPOLL3", "Status Unchanged")
                } else if (joinedExperiment.stage == AssessmentStage.COMPLETE.stage) {
                    stopCollection(experimentID, joinedExperiment.stage)
                    isAwaiting = false
                    Log.d("EXPPOLL3", "Status Changed to " + joinedExperiment.stage)
                    navController.navigate(Screen.Complete.route)
                } else {
                    Log.d("EXPPOLL3", "Something went wrong")
                    navController.navigate(Screen.JoinExperiment.route)
                }
                delay(1000)
            }
        }
    }


    override fun onCleared() {
        super.onCleared()
        sensorManager.stop()
    }

    fun uploadCollectedData(experimentId: String, state: String) {
        viewModelScope.launch {
            try {
                val metadata = DTOMetadata(state)
                val dataToUpload = SensorDTO(metadata, sensorManager.recordedData)  // Get data from your manager

                val response = Requestor.getSensorService().uploadSensorData(
                    experimentID = experimentId,
                    state = state,
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
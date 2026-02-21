package ca.carleton.rewatch.presentation.viewModels

import android.app.Application
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavController
import ca.carleton.rewatch.dataclasses.AssessmentStage
import ca.carleton.rewatch.dataclasses.JoinedExperiment
import ca.carleton.rewatch.presentation.AccelerometerManager
import ca.carleton.rewatch.presentation.Screen
import ca.carleton.rewatch.service.Requestor
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class CalibrationViewModel(application: Application, private val savedStateHandle: SavedStateHandle) : AndroidViewModel(application) {

    private val sensorManager = AccelerometerManager(application)
    var collectionText by mutableStateOf("Calibrating Watch")

    fun startCalibration() {
        sensorManager.start()
    }

    fun stopCalibration() {
        sensorManager.stop()
        // @TODO implement data transfer
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
                if (joinedExperiment?.stage == AssessmentStage.CALIBRATION.stage) {
                    Log.d("EXPPOLL2", "Awaiting Change to Status")
                } else if (joinedExperiment?.stage == AssessmentStage.CALIBRATION_COMPLETE.stage) {
                    stopCalibration()
                    Log.d("EXPPOLL2", "Calibration Complete Message")
                    collectionText = "Calibration Complete\nPlease Return"
                } else if (joinedExperiment?.stage == AssessmentStage.RT_TEST.stage) {
                    stopCalibration()
                    isAwaiting = false
                    Log.d("EXPPOLL2", "Status Changed to RT")
                    navController.navigate(Screen.RTTest.route.replace(
                        oldValue = "{experimentID}",
                        newValue = experimentID
                    ))
                } else {
                    isAwaiting = false
                    Log.d("EXPPOLL2", "Status Changed to " + joinedExperiment?.stage)
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
                val dataToUpload = sensorManager.recordedData // Get data from your manager

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